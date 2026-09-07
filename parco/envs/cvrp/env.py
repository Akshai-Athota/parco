from rl4co.utils.pylogger import get_pylogger

from parco.envs.hcvrp.env import HCVRPEnv

from .generator import CVRPGenerator

log = get_pylogger(__name__)


class CVRPEnv(HCVRPEnv):
    """Min-max Capacitated Vehicle Routing Problem with a HOMOGENEOUS fleet.

    Same problem as :class:`HCVRPEnv` with ``cap_m = cap`` for every vehicle m
    (and unit speed, so the objective is ``min max_m L_m`` in route length):

        min max_m L_m   s.t.   sum_{j in route_m} d_j <= cap   for all m

    Every dynamic here -- the transition, the action mask, the min-max reward --
    is inherited unchanged from HCVRP, because the heterogeneous formulation
    already covers the homogeneous case as the special case where all capacities
    coincide. Only the generator differs.

    This is deliberately the *only* new code: the encoder, communication layers,
    decoder, conflict handler and training loop are untouched, which makes this
    a clean test of whether PARCO's parallel decoding generalises beyond
    heterogeneous fleets.
    """

    name = "cvrp"

    def __init__(
        self,
        generator: CVRPGenerator = None,
        generator_params: dict = {},
        check_solution: bool = False,
        **kwargs,
    ):
        if generator is None:
            generator = CVRPGenerator(**generator_params)
        super().__init__(
            generator=generator,
            generator_params=generator_params,
            check_solution=check_solution,
            **kwargs,
        )
