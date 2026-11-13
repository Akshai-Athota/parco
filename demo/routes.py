"""Turn a model's raw actions into routes, timelines and fleet statistics.

Node indexing follows the HCVRP environment exactly: ``locs`` holds the depot
repeated once per agent and then the customers, so for M agents and N customers

    index 0 .. M-1      the depot, one copy per agent
    index M .. M+N-1    customer index - M

An agent "stays" by selecting the node it is already on, which the environment
treats as a no-op, so consecutive duplicates collapse. The environment adds the
final leg back to the depot when it computes the reward, so we do the same.

This module deliberately has no torch or rl4co import: it is pure arithmetic,
which keeps it testable without the training stack installed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import List, Sequence


def dist(a: Sequence[float], b: Sequence[float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


@dataclass
class Stop:
    """One visit in a vehicle's route."""
    node: int                 # index into the env's node list
    customer: int | None      # customer index, or None when it is the depot
    x: float
    y: float
    demand: float
    arrive_dist: float        # cumulative distance on arrival
    arrive_time: float        # cumulative time on arrival (distance / speed)
    load_after: float         # load carried after serving this stop


@dataclass
class VehicleRoute:
    vehicle: int
    capacity: float
    speed: float
    stops: List[Stop] = field(default_factory=list)
    distance: float = 0.0
    time: float = 0.0
    served: int = 0
    trips: int = 0            # depot departures = number of separate trips
    max_load: float = 0.0

    @property
    def utilisation(self) -> float:
        return 0.0 if self.capacity <= 0 else self.max_load / self.capacity


@dataclass
class Plan:
    method: str
    routes: List[VehicleRoute]
    objective: float          # max_m (distance_m / speed_m) -- what the model minimises
    total_distance: float
    steps: int                # decoder passes
    elapsed_ms: float
    served: int
    note: str = ""

    def to_json(self) -> dict:
        d = asdict(self)
        d["utilisation"] = [round(r.utilisation, 4) for r in self.routes]
        return d


def collapse(seq: Sequence[int], start: int) -> List[int]:
    """Drop consecutive repeats (the environment's no-op) starting from ``start``."""
    out = [start]
    for a in seq:
        if a != out[-1]:
            out.append(int(a))
    return out


def build_plan(
    method: str,
    actions: Sequence[Sequence[int]],   # [M][T] node indices
    depot: Sequence[float],
    customers: Sequence[dict],          # [{x, y, demand}]
    vehicles: Sequence[dict],           # [{capacity, speed}]
    steps: int,
    elapsed_ms: float,
    note: str = "",
) -> Plan:
    """Reconstruct per-vehicle routes and the min-max objective from raw actions."""
    m_count = len(vehicles)
    coords = [tuple(depot)] * m_count + [(c["x"], c["y"]) for c in customers]
    demands = [0.0] * m_count + [float(c["demand"]) for c in customers]

    routes: List[VehicleRoute] = []
    served_nodes: set[int] = set()

    for m, veh in enumerate(vehicles):
        speed = float(veh["speed"]) or 1.0
        seq = collapse(actions[m], start=m)
        # the environment closes the tour at the depot when scoring
        if seq[-1] != m:
            seq.append(m)

        route = VehicleRoute(vehicle=m, capacity=float(veh["capacity"]), speed=speed)
        cum_d = 0.0
        load = 0.0
        for i, node in enumerate(seq):
            if i > 0:
                cum_d += dist(coords[seq[i - 1]], coords[node])
            is_depot = node < m_count
            if is_depot:
                load = 0.0
                if i > 0 and i < len(seq) - 1:
                    route.trips += 1
            else:
                load += demands[node]
                route.served += 1
                served_nodes.add(node)
            route.max_load = max(route.max_load, load)
            route.stops.append(
                Stop(
                    node=node,
                    customer=None if is_depot else node - m_count,
                    x=coords[node][0], y=coords[node][1],
                    demand=demands[node],
                    arrive_dist=round(cum_d, 6),
                    arrive_time=round(cum_d / speed, 6),
                    load_after=round(load, 3),
                )
            )
        route.distance = round(cum_d, 6)
        route.time = round(cum_d / speed, 6)
        if route.served:
            route.trips += 1
        routes.append(route)

    return Plan(
        method=method,
        routes=routes,
        objective=round(max((r.time for r in routes), default=0.0), 6),
        total_distance=round(sum(r.distance for r in routes), 6),
        steps=steps,
        elapsed_ms=round(elapsed_ms, 2),
        served=len(served_nodes),
        note=note,
    )


def validity(plan: Plan, n_customers: int) -> dict:
    """Check the plan actually solves the instance. Surfaced in the UI."""
    served: list[int] = []
    over = []
    for r in plan.routes:
        for s in r.stops:
            if s.customer is not None:
                served.append(s.customer)
        if r.max_load > r.capacity + 1e-6:
            over.append({"vehicle": r.vehicle, "load": r.max_load, "capacity": r.capacity})
    uniq = set(served)
    return {
        "all_served": len(uniq) == n_customers,
        "missing": sorted(set(range(n_customers)) - uniq),
        "duplicates": len(served) - len(uniq),
        "capacity_violations": over,
        "ok": len(uniq) == n_customers and not over and len(served) == len(uniq),
    }
