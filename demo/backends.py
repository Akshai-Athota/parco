"""Planners behind the demo.

Two backends share one interface so the web app is identical either way:

``HeuristicBackend``  a min-max nearest-neighbour planner. No torch, no rl4co,
                      no checkpoints. It exists so the interface, the route
                      reconstruction and the whole UI can be exercised on a
                      laptop, and so the demo still runs if the training stack
                      is unavailable. It is a reference point, not one of our
                      methods, and the UI labels it as such.

``TorchBackend``      the real thing: loads the trained checkpoints and runs
                      the policy. Imports torch/rl4co lazily so that merely
                      importing this module costs nothing.
"""

from __future__ import annotations

import math
import os
import time
from typing import Dict, List, Sequence

from routes import Plan, build_plan, dist

# name -> (run folder under RUNS_ROOT, decode family, decode_k, label, colour)
METHODS: Dict[str, dict] = {
    "parallel": dict(run="parco_tanh_fixed_g10_t1_attn0_lr0.0001", family="plain",
                     k=None, label="Parallel PARCO", colour="#2E5C8A",
                     blurb="All M agents commit per pass; a priority rule repairs collisions."),
    "k1": dict(run="parco_k1", family="kparallel", k=1, label="k = 1 (sequential)",
               colour="#E2561F",
               blurb="One (agent, node) pair per pass. Every decision sees all previous ones."),
    "k2": dict(run="parco_k2", family="kparallel", k=2, label="k = 2",
               colour="#12927A",
               blurb="Two pairs per pass. Beat PARCO on all 12 test sets using less compute."),
    "k4": dict(run="parco_k4", family="kparallel", k=4, label="k = 4",
               colour="#7E5AA8", blurb="Four pairs per pass -- a speed point on the front."),
    "k7": dict(run="parco_k7", family="kparallel", k=7, label="k = 7 (joint)",
               colour="#6B8299",
               blurb="All agents from one pass, collision-free but on stale logits."),
    "tanh": dict(run="parco_tanh_scaled_g10_t1_attn0_lr0.0001", family="plain", k=None,
                 label="Tanh scaled", colour="#D9A21B",
                 blurb="Parallel PARCO with the corrected clip 10*tanh(z/10)."),
}

DEFAULT_RUNS_ROOT = "logs/train/runs/hcvrp_n100_m7"


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_runs_root(runs_root: str) -> str:
    """Accept a relative runs root whether the server is started from the repo
    root or from inside demo/."""
    if os.path.isabs(runs_root) or os.path.isdir(runs_root):
        return runs_root
    candidate = os.path.join(REPO_ROOT, runs_root)
    return candidate if os.path.isdir(candidate) else runs_root


def resolve_checkpoint(runs_root: str, run: str) -> str | None:
    folder = os.path.join(resolve_runs_root(runs_root), run)
    if not os.path.isdir(folder):
        return None
    found = [
        os.path.join(folder, ts, "checkpoints", "last.ckpt")
        for ts in os.listdir(folder)
        if os.path.exists(os.path.join(folder, ts, "checkpoints", "last.ckpt"))
    ]
    return max(found, key=os.path.getmtime) if found else None


# --------------------------------------------------------------------------- #
class HeuristicBackend:
    """Min-max nearest neighbour: always advance whichever vehicle is furthest behind."""

    name = "heuristic"

    def available(self) -> List[str]:
        return ["heuristic"]

    def describe(self) -> Dict[str, dict]:
        return {"heuristic": dict(
            label="Nearest neighbour", colour="#94A3B8",
            blurb="Classical baseline, not one of our models: repeatedly move the "
                  "vehicle that is furthest behind to its nearest feasible order.")}

    def plan(self, scenario: dict, methods: Sequence[str]) -> Dict[str, Plan]:
        return {m: self._solve(scenario) for m in methods if m == "heuristic"}

    def _solve(self, sc: dict) -> Plan:
        t0 = time.perf_counter()
        depot, custs, vehs = sc["depot"], sc["customers"], sc["vehicles"]
        M, N = len(vehs), len(custs)
        pos = [(depot["x"], depot["y"])] * M
        load = [0.0] * M
        clock = [0.0] * M
        actions: List[List[int]] = [[] for _ in range(M)]
        unvisited = set(range(N))
        steps = 0

        while unvisited and steps < 4 * (N + M) + 50:
            steps += 1
            m = min(range(M), key=lambda i: clock[i])
            cap_left = vehs[m]["capacity"] - load[m]
            feasible = [c for c in unvisited if custs[c]["demand"] <= cap_left + 1e-9]
            if not feasible:
                # no order fits: go back to the depot and reload
                d = dist(pos[m], (depot["x"], depot["y"]))
                clock[m] += d / vehs[m]["speed"]
                pos[m] = (depot["x"], depot["y"])
                load[m] = 0.0
                actions[m].append(m)
                continue
            c = min(feasible, key=lambda c: dist(pos[m], (custs[c]["x"], custs[c]["y"])))
            d = dist(pos[m], (custs[c]["x"], custs[c]["y"]))
            clock[m] += d / vehs[m]["speed"]
            pos[m] = (custs[c]["x"], custs[c]["y"])
            load[m] += custs[c]["demand"]
            unvisited.discard(c)
            actions[m].append(M + c)

        return build_plan(
            "heuristic", actions, (depot["x"], depot["y"]), custs, vehs,
            steps=steps, elapsed_ms=(time.perf_counter() - t0) * 1000,
            note="classical baseline" if not unvisited else "incomplete: no feasible assignment",
        )


# --------------------------------------------------------------------------- #
class TorchBackend:
    """Runs the trained PARCO / k-parallel checkpoints."""

    name = "torch"

    def __init__(self, runs_root: str = DEFAULT_RUNS_ROOT, device: str = "cpu"):
        self.runs_root = runs_root
        self.device_str = device
        self._cache: dict = {}
        self._env = None
        # Import the stack up front rather than on the first solve: a missing
        # dependency should be a clear message at startup, not a failure in
        # front of an audience.
        import torch                   # noqa: F401
        import tensordict             # noqa: F401
        from parco.models import PARCORLModule   # noqa: F401
        from parco.envs import HCVRPEnv          # noqa: F401

        self._found = {
            key: path
            for key, cfg in METHODS.items()
            if (path := resolve_checkpoint(runs_root, cfg["run"])) is not None
        }

    def available(self) -> List[str]:
        return list(self._found)

    def describe(self) -> Dict[str, dict]:
        return {
            k: {kk: METHODS[k][kk] for kk in ("label", "colour", "blurb")}
            for k in self._found
        }

    # -- lazy heavy imports -------------------------------------------------
    def _load(self, key: str):
        if key in self._cache:
            return self._cache[key]
        import torch
        from parco.models import PARCORLModule

        model = PARCORLModule.load_from_checkpoint(
            self._found[key], map_location="cpu", strict=False
        )
        policy = model.policy.to(torch.device(self.device_str)).eval()
        self._cache[key] = policy
        return policy

    def _environment(self):
        if self._env is None:
            from parco.envs import HCVRPEnv
            self._env = HCVRPEnv()
        return self._env

    def _tensordict(self, sc: dict):
        import torch
        from tensordict import TensorDict

        depot, custs, vehs = sc["depot"], sc["customers"], sc["vehicles"]
        t = lambda v: torch.tensor(v, dtype=torch.float32)  # noqa: E731
        return TensorDict(
            {
                "locs": t([[[c["x"], c["y"]] for c in custs]]),
                "depot": t([[depot["x"], depot["y"]]]),
                "demand": t([[c["demand"] for c in custs]]),
                "capacity": t([[v["capacity"] for v in vehs]]),
                "speed": t([[v["speed"] for v in vehs]]),
            },
            batch_size=[1],
        )

    def plan(self, scenario: dict, methods: Sequence[str]) -> Dict[str, Plan]:
        import torch

        env = self._environment()
        device = torch.device(self.device_str)
        out: Dict[str, Plan] = {}

        for key in methods:
            if key not in self._found:
                continue
            cfg = METHODS[key]
            policy = self._load(key)
            decode_type = (
                "kparallel_greedy" if cfg["family"] == "kparallel" else "greedy"
            )
            extra = {"decode_k": cfg["k"]} if cfg["k"] is not None else {}

            td = env.reset(self._tensordict(scenario)).to(device)
            t0 = time.perf_counter()
            with torch.inference_mode():
                res = policy(td, env, decode_type=decode_type,
                             return_actions=True, **extra)
            elapsed = (time.perf_counter() - t0) * 1000

            acts = res["actions"][0].cpu().tolist()   # [M][T]
            plan = build_plan(
                key, acts,
                (scenario["depot"]["x"], scenario["depot"]["y"]),
                scenario["customers"], scenario["vehicles"],
                steps=int(res.get("steps", len(acts[0]))),
                elapsed_ms=elapsed,
            )
            # the environment's own reward is the ground truth -- compare, never assume
            reward = float(res["reward"][0])
            plan.note = _reward_check(plan.objective, -reward)
            out[key] = plan
        return out


def _reward_check(objective: float, env_objective: float) -> str:
    if math.isclose(objective, env_objective, rel_tol=1e-4, abs_tol=1e-5):
        return ""
    return (f"reconstructed {objective:.4f} vs environment {env_objective:.4f} "
            f"-- route drawing may be out of step with the score")


# --------------------------------------------------------------------------- #
class CompositeBackend:
    """Torch methods when the stack is importable, plus the heuristic reference."""

    def __init__(self, runs_root: str = DEFAULT_RUNS_ROOT, device: str = "cpu",
                 force_mock: bool = False):
        self.heuristic = HeuristicBackend()
        self.torch = None
        self.reason = ""
        if force_mock:
            self.reason = "started with --mock"
            return
        try:
            self.torch = TorchBackend(runs_root, device)
            if not self.torch.available():
                self.reason = f"no checkpoints found under {runs_root}"
                self.torch = None
        except Exception as exc:  # torch / rl4co / parco missing
            self.reason = f"{type(exc).__name__}: {exc}"
            self.torch = None

    def describe(self) -> Dict[str, dict]:
        d = dict(self.heuristic.describe())
        if self.torch:
            d = {**self.torch.describe(), **d}
        return d

    def plan(self, scenario: dict, methods: Sequence[str]) -> Dict[str, Plan]:
        out: Dict[str, Plan] = {}
        if self.torch:
            out.update(self.torch.plan(scenario, [m for m in methods if m != "heuristic"]))
        out.update(self.heuristic.plan(scenario, [m for m in methods if m == "heuristic"]))
        return out
