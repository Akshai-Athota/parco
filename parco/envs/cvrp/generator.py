from typing import Callable, Union

import torch

from rl4co.utils.pylogger import get_pylogger
from tensordict.tensordict import TensorDict
from torch.distributions import Uniform

from parco.envs.hcvrp.generator import HCVRPGenerator

log = get_pylogger(__name__)


class CVRPGenerator(HCVRPGenerator):
    """Data generator for the min-max CVRP with a HOMOGENEOUS fleet.

    Identical to :class:`HCVRPGenerator` except that the fleet is uniform:

    - every vehicle gets the same capacity ``cap_m = capacity`` for all m,
      instead of ``capacity ~ U(20, 41)`` drawn per vehicle;
    - every vehicle gets unit speed, so the min-max objective is the longest
      route *length* ``max_m L_m`` rather than the longest travel *time*
      ``max_m L_m / f_m``.

    Everything else -- locations, depot, integer demands in [1, 9] -- is
    unchanged, so the only difference from HCVRP is fleet homogeneity. This is
    what makes the comparison a clean test of whether parallel decoding is a
    general-purpose mechanism or a heterogeneous-fleet-specific one.

    Args:
        capacity: the single capacity shared by all vehicles. The default of 50
            follows the usual CVRP benchmark convention (Kool et al., POMO) for
            N=100 with demands in [1, 9]. A single value is used for every
            problem size so that one trained model sees a consistent capacity.
        speed: the single speed shared by all vehicles. Leave at 1.0 to keep the
            objective equal to route length.
    """

    def __init__(
        self,
        num_loc: int = 100,
        min_loc: float = 0.0,
        max_loc: float = 1.0,
        loc_distribution: Union[int, float, str, type, Callable] = Uniform,
        depot_distribution: Union[int, float, str, type, Callable] = None,
        min_demand: int = 1,
        max_demand: int = 10,
        demand_distribution: Union[int, float, type, Callable] = Uniform,
        capacity: float = 50.0,
        speed: float = 1.0,
        num_agents: int = 3,
        scale_data: bool = False,  # leave False!
        **kwargs,
    ):
        # Capacity and speed are constants here, so the corresponding samplers of
        # the parent generator are never used; we still initialise the parent so
        # that the location / demand samplers behave identically to HCVRP.
        super().__init__(
            num_loc=num_loc,
            min_loc=min_loc,
            max_loc=max_loc,
            loc_distribution=loc_distribution,
            depot_distribution=depot_distribution,
            min_demand=min_demand,
            max_demand=max_demand,
            demand_distribution=demand_distribution,
            min_capacity=capacity,
            max_capacity=capacity,
            min_speed=speed,
            max_speed=speed,
            num_agents=num_agents,
            scale_data=scale_data,
            **kwargs,
        )
        self.capacity = capacity
        self.speed = speed

    def _generate(self, batch_size) -> TensorDict:
        # Sample locations: depot and customers
        if self.depot_sampler is not None:
            depot = self.depot_sampler.sample((*batch_size, 2))
            locs = self.loc_sampler.sample((*batch_size, self.num_loc, 2))
        else:
            # If depot_sampler is None, sample the depot from the locations
            locs = self.loc_sampler.sample((*batch_size, self.num_loc + 1, 2))
            depot = locs[..., 0, :]
            locs = locs[..., 1:, :]

        # Sample demands, exactly as in HCVRP
        demand = self.demand_sampler.sample((*batch_size, self.num_loc))
        demand = (demand.int() + 1).float()

        # Homogeneous fleet: constant capacity and speed for every vehicle
        capacity = torch.full(
            (*batch_size, self.num_agents), self.capacity, dtype=torch.float32
        )
        speed = torch.full(
            (*batch_size, self.num_agents), self.speed, dtype=torch.float32
        )

        return TensorDict(
            {
                "locs": locs,
                "depot": depot,
                "num_agents": torch.full((*batch_size,), self.num_agents),
                "demand": demand / self.capacity if self.scale_data else demand,
                "capacity": capacity / self.capacity if self.scale_data else capacity,
                "speed": speed / self.speed if self.scale_data else speed,
            },
            batch_size=batch_size,
        )
