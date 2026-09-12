import abc

from typing import Tuple

import torch
import torch.nn.functional as F

from einops import rearrange
from rl4co.envs import RL4COEnvBase
from rl4co.utils.decoding import process_logits
from rl4co.utils.ops import batchify, gather_by_index, unbatchify, unbatchify_and_gather
from rl4co.utils.pylogger import get_pylogger
from tensordict.tensordict import TensorDict

log = get_pylogger(__name__)


def parco_get_decoding_strategy(decoding_strategy, **config):
    strategy_registry = {
        "greedy": Greedy,
        "sampling": Sampling,
        "evaluate": Evaluate,
        "joint_greedy": JointGreedy,
        "joint_sampling": JointSampling,
    }

    if "multistart" in decoding_strategy:
        # raise ValueError("Multistart is not supported for multi-agent decoding")
        decoding_strategy = decoding_strategy.split("_")[-1]

    if decoding_strategy not in strategy_registry:
        log.warning(
            f"Unknown decode type '{decoding_strategy}'. Available decode types: {strategy_registry.keys()}. Defaulting to Sampling."
        )

    return strategy_registry.get(decoding_strategy, Sampling)(**config)


class PARCODecodingStrategy(metaclass=abc.ABCMeta):
    name = "base"

    def __init__(
        self,
        num_agents: int,
        agent_handler=None,  # Agent handler
        use_init_logp: bool = True,  # Return initial logp for actions even with conflicts
        mask_handled: bool = False,  # Mask out handled actions (make logprobs 0)
        replacement_value_key: str = "current_node",  # When stopping arises (conflict or POS token), replace the value of this key
        temperature: float = 1.0,
        top_p: float = 0.0,
        top_k: int = 0,
        tanh_clipping: float = 10.0,
        multistart: bool = False,
        multisample: bool = False,
        num_samples: int = 1,
        select_best: bool = False,
        store_all_logp: bool = False,
        store_handling_mask: bool = False,  # TODO: check - memory issue?
    ) -> None:
        # PARCO-related
        if mask_handled and agent_handler is None:
            raise ValueError(
                "mask_handled is only supported when agent_handler is not None for now"
            )

        if store_all_logp and mask_handled:
            raise ValueError("store_all_logp is not supported when mask_handled is True")

        if mask_handled and use_init_logp:
            raise ValueError(
                "We should not mask out the initial action logp, rather the final action logp"
            )

        self.use_init_logp = use_init_logp
        self.mask_handled = mask_handled
        self.store_all_logp = store_all_logp
        self.store_handling_mask = store_handling_mask
        self.num_agents = num_agents
        self.agent_handler = agent_handler
        self.replacement_value_key = replacement_value_key

        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.tanh_clipping = tanh_clipping
        if multistart:
            raise ValueError("Multistart is not supported for multi-agent decoding")
        self.multistart = multistart
        self.multisample = multisample
        self.num_samples = num_samples
        if self.num_samples > 1:
            self.multisample = True
        self.select_best = select_best

        # initialize buffers
        self.actions = []
        self.logprobs = []
        self.handling_masks = []
        self.halting_ratios = []
        self.iter_count = 0

    @abc.abstractmethod
    def _step(
        self,
        logprobs: torch.Tensor,
        mask: torch.Tensor,
        td: TensorDict,
        action: torch.Tensor = None,
        **kwargs,
    ) -> Tuple[torch.Tensor, torch.Tensor, TensorDict]:
        raise NotImplementedError("Must be implemented by subclass")

    def pre_decoder_hook(
        self, td: TensorDict, env: RL4COEnvBase, action: torch.Tensor = None
    ):
        """Pre decoding hook. This method is called before the main decoding operation."""

        if self.num_samples >= 1:
            # Expand td to batch_size * num_samples
            td = batchify(td, self.num_samples)

        return td, env, self.num_samples  # TODO: check

    def post_decoder_hook(
        self, td: TensorDict, env: RL4COEnvBase
    ) -> Tuple[torch.Tensor, torch.Tensor, TensorDict, RL4COEnvBase]:
        """ "
        Size depends on whether we store all log p or not. By default, we don't
        Returns:
            logprobs: [B, m, L]
            actions: [B, m, L]
        """
        assert (
            len(self.logprobs) > 0
        ), "No logprobs were collected because all environments were done. Check your initial state"
        # [B, m, L] (or is it?)
        logprobs = torch.stack(self.logprobs, -1)
        actions = torch.stack(self.actions, -1)

        if len(self.handling_masks) > 0:
            if self.handling_masks[0] is not None:
                self.handling_masks = torch.stack(self.handling_masks, 2)
            else:
                pass
        else:
            pass

        halting_ratios = (
            torch.stack(self.halting_ratios, 0) if len(self.halting_ratios) > 0 else 0
        )

        if self.num_samples > 0 and self.select_best:
            logprobs, actions, td, env = self._select_best(logprobs, actions, td, env)

        return logprobs, actions, td, env, halting_ratios

    def step(
        self,
        logits: torch.Tensor,
        mask: torch.Tensor,
        td: TensorDict = None,
        agent_handler_kwargs: dict = {},
        **kwargs,
    ) -> TensorDict:
        self.iter_count += 1

        logprobs = process_logits(
            logits,
            mask,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            tanh_clipping=self.tanh_clipping,
        )

        logprobs, actions, td = self._step(logprobs, mask, td, **kwargs)
        actions_init = actions.clone()

        # Solve conflicts via agent handler
        replacement_value = td[self.replacement_value_key]  # replace with previous node

        actions, handling_mask, halting_ratio = self.agent_handler(
            actions, replacement_value, td, probs=logprobs.clone(), **agent_handler_kwargs
        )
        if self.store_handling_mask:
            # NOTE
            # this might be used for some PARCO improvements (i.e. during training)\
            # but will increase memory usage by a TON
            self.handling_masks.append(handling_mask)
        self.halting_ratios.append(halting_ratio)

        # for others
        if not self.store_all_logp:
            actions_gather = actions_init if self.use_init_logp else actions
            # logprobs: [B, m, N], actions_cur: [B, m]
            # transform logprobs to [B, m]

            logprobs = gather_by_index(logprobs, actions_gather, dim=-1)

            # We do this after gathering the logprobs
            if self.mask_handled:
                logprobs.masked_fill_(handling_mask, 0)

        td.set("action", actions)
        self.actions.append(actions)
        self.logprobs.append(logprobs)
        return td

    @staticmethod
    def greedy(logprobs, mask=None):
        """Select the action with the highest probability."""
        selected = logprobs.argmax(dim=-1)  # [B, m, N] -> [B, m]
        if mask is not None:  # [B, m, N]
            assert (
                not (~mask).gather(-1, selected.unsqueeze(-1)).data.any()
            ), "infeasible action selected"
        return selected

    @staticmethod
    def sampling(logprobs, mask=None):
        """Sample an action with a multinomial distribution given by the log probabilities."""

        distribution = torch.distributions.Categorical(logits=logprobs)
        selected = distribution.sample()  # samples [B, m, N] -> [B, m]

        if mask is not None:
            # checking for bad values sampling; but is this needed?
            while (~mask).gather(-1, selected.unsqueeze(-1)).data.any():
                log.info("Sampled bad values, resampling!")
                # selected = probs.multinomial(1).squeeze(1)
                selected = distribution.sample()
            assert (
                not (~mask).gather(-1, selected.unsqueeze(-1)).data.any()
            ), "infeasible action selected"
        return selected

    def _select_best(self, logprobs, actions, td: TensorDict, env: RL4COEnvBase):
        # TODO: check
        rewards = env.get_reward(td, actions)
        _, max_idxs = unbatchify(rewards, self.num_samples).max(dim=-1)

        actions = unbatchify_and_gather(actions, max_idxs, self.num_samples)
        logprobs = unbatchify_and_gather(logprobs, max_idxs, self.num_samples)
        td = unbatchify_and_gather(td, max_idxs, self.num_samples)

        return logprobs, actions, td, env


class Greedy(PARCODecodingStrategy):
    name = "greedy"

    def _step(
        self, logprobs: torch.Tensor, mask: torch.Tensor, td: TensorDict, **kwargs
    ) -> Tuple[torch.Tensor, torch.Tensor, TensorDict]:
        """Select the action with the highest log probability"""
        selected = self.greedy(logprobs, mask)
        return logprobs, selected, td


class Sampling(PARCODecodingStrategy):
    name = "sampling"

    def _step(
        self, logprobs: torch.Tensor, mask: torch.Tensor, td: TensorDict, **kwargs
    ) -> Tuple[torch.Tensor, torch.Tensor, TensorDict]:
        """Sample an action with a multinomial distribution given by the log probabilities."""
        selected = self.sampling(logprobs, mask)
        return logprobs, selected, td


class Evaluate(PARCODecodingStrategy):
    name = "evaluate"

    def _step(
        self,
        logprobs: torch.Tensor,
        mask: torch.Tensor,
        td: TensorDict,
        action: torch.Tensor,
        **kwargs,
    ) -> Tuple[torch.Tensor, torch.Tensor, TensorDict]:
        """The action is provided externally, so we just return the action"""
        selected = action
        return logprobs, selected, td


class MaskedJointDecodingStrategy(PARCODecodingStrategy):
    """Collision-free joint decoding from a single decoder pass.

    Parallel PARCO samples the M agents independently and repairs the collisions
    afterwards, so the action the policy scored (the proposal) is not the action
    the environment executed. Sequential decoding removes that gap but pays for
    it with one decoder pass per agent assignment.

    This is the middle ground. The [B, M, A] logits are computed ONCE per
    environment step, then agents are assigned one at a time from the flattened
    joint distribution: after each pick, that agent's row and that node's column
    are masked out, so no two agents can be handed the same node. All M agents
    still act in the same environment step, so an episode has the same number of
    steps as parallel PARCO -- the inner loop is just masking and argmax over a
    matrix that already exists.

    Two consequences:

    - the sampled joint action IS the executed one, so the proposal and executed
      distributions coincide and no conflict handler is needed;
    - the joint logprob is the sum of the M sequential conditionals, which is a
      proper distribution over collision-free assignments.

    The cost relative to sequential decoding is staleness: the second and later
    agents choose from logits computed before the earlier assignments existed.
    That gap is exactly what the ablation against `sequential_greedy` measures.
    """

    def _select_flat(self, flat_logprobs: torch.Tensor) -> torch.Tensor:
        """Pick one flattened (agent, node) index per instance. Returns [B]."""
        raise NotImplementedError("Must be implemented by subclass")

    def step(
        self,
        logits: torch.Tensor,
        mask: torch.Tensor,
        td: TensorDict = None,
        agent_handler_kwargs: dict = {},
        **kwargs,
    ) -> TensorDict:
        self.iter_count += 1
        batch_size, num_agents, num_actions = logits.shape

        if self.tanh_clipping > 0:
            logits = self.tanh_clipping * torch.tanh(logits)

        work_mask = mask.clone()
        # Agents not reached by the loop keep their current node, which the env
        # treats as a no-op through its stay_flag
        actions = td["current_node"].clone()
        logprobs = torch.zeros(
            (batch_size, num_agents), dtype=torch.float32, device=logits.device
        )

        for _ in range(num_agents):
            masked_logits = logits.masked_fill(~work_mask, -torch.inf)
            flat = masked_logits.reshape(batch_size, -1)

            # Instances with no assignable (agent, node) pair left: the neutral
            # row keeps log_softmax finite and the result is discarded below
            exhausted = ~torch.isfinite(flat).any(dim=-1)
            flat = torch.where(exhausted[:, None], torch.zeros_like(flat), flat)

            flat_logprobs = F.log_softmax(flat / self.temperature, dim=-1)
            flat_action = self._select_flat(flat_logprobs)  # [B]
            selected_logprob = flat_logprobs.gather(1, flat_action[:, None]).squeeze(1)

            agent_idx = torch.div(flat_action, num_actions, rounding_mode="floor")
            node_idx = flat_action % num_actions
            live = (~exhausted)[:, None]

            actions = torch.where(
                live,
                actions.scatter(1, agent_idx[:, None], node_idx[:, None]),
                actions,
            )
            step_logprob = torch.zeros_like(logprobs).scatter(
                1, agent_idx[:, None], selected_logprob[:, None].float()
            )
            logprobs = logprobs + torch.where(
                live, step_logprob, torch.zeros_like(step_logprob)
            )

            # That agent is now assigned, and that node is taken. Depot indices
            # are per-agent (the env masks them with an identity matrix), so
            # clearing a depot column never blocks another agent's own depot.
            work_mask = work_mask.scatter(
                1, agent_idx[:, None, None].expand(-1, 1, num_actions), False
            )
            work_mask = work_mask.scatter(
                2, node_idx[:, None, None].expand(-1, num_agents, 1), False
            )

        # Collisions are impossible by construction, so no conflict is handled
        self.halting_ratios.append(torch.zeros((), device=logits.device))

        td.set("action", actions)
        self.actions.append(actions)
        self.logprobs.append(logprobs)
        return td

    def _step(self, logprobs, mask, td, action=None, **kwargs):
        """Unused: ``step`` is overridden wholesale."""


class JointGreedy(MaskedJointDecodingStrategy):
    name = "joint_greedy"

    def _select_flat(self, flat_logprobs: torch.Tensor) -> torch.Tensor:
        return flat_logprobs.argmax(dim=-1)


class JointSampling(MaskedJointDecodingStrategy):
    name = "joint_sampling"

    def _select_flat(self, flat_logprobs: torch.Tensor) -> torch.Tensor:
        return torch.distributions.Categorical(logits=flat_logprobs).sample()


class PARCO4FFSPDecoding(PARCODecodingStrategy):

    def __init__(
        self,
        num_ma,
        num_job,
        use_pos_token: bool = False,
        tanh_clipping: float = 10.0,
        num_stages: int = 3,
    ) -> None:
        super().__init__(num_agents=num_ma)
        self.num_ma = num_ma // num_stages
        self.num_job = num_job
        self.use_pos_token = use_pos_token
        self.tanh_clipping = tanh_clipping or 1
        self.num_stages = num_stages

    def step(
        self, logits: torch.Tensor, mask: torch.Tensor, td: TensorDict = None, **kwargs
    ) -> TensorDict:

        batch_size = td.batch_size
        device = td.device

        if self.tanh_clipping > 1:
            logits = self.tanh_clipping * torch.tanh(logits)
        step_mask = ~mask.clone()
        step_mask[..., -1] = ~step_mask[..., :-1].all((1, 2)).unsqueeze(1)
        idle_machines = torch.arange(0, self.num_ma, device=device)[None, :].expand(
            *batch_size, -1
        )

        step_actions = torch.full(
            (*batch_size, self.num_ma),
            fill_value=self.num_job,
            device=device,
            dtype=torch.long,
        )
        step_logp = torch.zeros_like(step_actions, dtype=torch.float32)
        while not step_mask[..., :-1].all():
            # get the probabilities of all actions given the current mask
            logits_masked = logits.masked_fill(step_mask, -torch.inf)
            logits_reshaped = rearrange(logits_masked, "b m j -> b (j m)")
            rollout_logprobs = F.log_softmax(logits_reshaped, dim=-1)
            # perform decoding
            # shape: (batch * pomo)
            selected_action = rollout_logprobs.exp().multinomial(1).squeeze(1)
            action_logprob = rollout_logprobs.gather(
                1, selected_action.unsqueeze(1)
            ).squeeze(1)

            # translate the action
            # shape: (batch * pomo)
            job_selected = selected_action // self.num_ma
            selected_machine = selected_action % self.num_ma
            # determine which machines still have to select an action
            idle_machines = idle_machines[
                idle_machines != selected_machine[:, None]
            ].view(*batch_size, -1)

            step_actions.scatter_(
                dim=1, index=selected_machine[:, None], src=job_selected[:, None]
            )
            step_logp.scatter_(
                dim=1, index=selected_machine[:, None], src=action_logprob[:, None]
            )
            # mask job that has been selected in the current step so it cannot be selected by other agents
            step_mask = step_mask.scatter(
                -1, job_selected.view(*batch_size, 1, 1).expand(-1, self.num_ma, 1), True
            )
            if self.use_pos_token:
                # allow machines that are still idle to wait (for jobs to become available for example)
                step_mask[..., -1] = step_mask[..., -1].scatter(
                    -1, idle_machines.view(*batch_size, -1), False
                )
            else:
                step_mask[..., -1] = step_mask[..., -1].scatter(
                    -1,
                    idle_machines.view(*batch_size, -1),
                    ~(step_mask[..., :-1].all(-1)),
                )
            # lastly, mask all actions for the selected agent
            step_mask = step_mask.scatter(
                -2,
                selected_machine.view(*batch_size, 1, 1).expand(-1, 1, self.num_job + 1),
                True,
            )

        self.actions.append(step_actions)
        self.logprobs.append(step_logp)

        td.set("action", step_actions)
        return td

    def _step(self, logprobs, mask, td, action=None, **kwargs):
        pass
