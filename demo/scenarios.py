"""Scenario generation and sanity checks for the delivery demo.

The checkpoints were trained on a specific distribution. Anything far outside it
is still solvable, but the result says more about generalisation than about the
method, so ``check`` returns warnings that the UI shows next to the map rather
than silently producing a number that looks comparable and is not.

Training distribution (HCVRPGenerator):
    customers   N ~ U(60, 100) during training, coordinates U(0,1)^2
    demand      integers 1..9
    fleet       M ~ U(3, 7), capacity U(20, 41), speed U(0.5, 1.0)
"""

from __future__ import annotations

import random
from typing import List

TRAIN = dict(n=(60, 100), m=(3, 7), demand=(1, 9), capacity=(20, 41), speed=(0.5, 1.0))


def _round(v: float, nd: int = 4) -> float:
    return round(float(v), nd)


def make_vehicles(m: int, rng: random.Random) -> List[dict]:
    return [
        {"capacity": _round(rng.uniform(*TRAIN["capacity"]), 1),
         "speed": _round(rng.uniform(*TRAIN["speed"]), 3)}
        for _ in range(m)
    ]


def _uniform(n, rng):
    return [(rng.random(), rng.random()) for _ in range(n)]


def _clusters(n, rng, k=3, spread=0.09):
    centres = [(rng.uniform(0.15, 0.85), rng.uniform(0.15, 0.85)) for _ in range(k)]
    pts = []
    for i in range(n):
        cx, cy = centres[i % k]
        pts.append((min(max(rng.gauss(cx, spread), 0.0), 1.0),
                    min(max(rng.gauss(cy, spread), 0.0), 1.0)))
    return pts


def _two_districts(n, rng):
    return _clusters(n, rng, k=2, spread=0.08)


def _ring(n, rng):
    import math
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.gauss(0, 0.08)
        r = 0.36 + rng.gauss(0, 0.045)
        pts.append((min(max(0.5 + r * math.cos(a), 0.0), 1.0),
                    min(max(0.5 + r * math.sin(a), 0.0), 1.0)))
    return pts


LAYOUTS = {
    "uniform": ("Uniform city", _uniform),
    "clusters": ("Three neighbourhoods", _clusters),
    "districts": ("Two districts", _two_districts),
    "ring": ("Ring road", _ring),
}


def generate(n: int = 40, m: int = 4, layout: str = "uniform",
             seed: int | None = None) -> dict:
    rng = random.Random(seed)
    _, fn = LAYOUTS.get(layout, LAYOUTS["uniform"])
    pts = fn(n, rng)
    return {
        "depot": {"x": 0.5, "y": 0.5},
        "customers": [
            {"x": _round(x), "y": _round(y),
             "demand": rng.randint(*TRAIN["demand"])}
            for x, y in pts
        ],
        "vehicles": make_vehicles(m, rng),
        "layout": layout,
        "seed": seed,
    }


def check(sc: dict) -> dict:
    """Hard errors block solving; warnings are shown but do not block."""
    errors: List[str] = []
    warnings: List[str] = []

    custs, vehs = sc.get("customers", []), sc.get("vehicles", [])
    n, m = len(custs), len(vehs)

    if n == 0:
        errors.append("Add at least one order.")
    if m == 0:
        errors.append("Add at least one vehicle.")
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    total_demand = sum(c["demand"] for c in custs)
    biggest_vehicle = max(v["capacity"] for v in vehs)
    biggest_order = max(c["demand"] for c in custs)
    if biggest_order > biggest_vehicle:
        errors.append(
            f"Order of {biggest_order} exceeds every vehicle's capacity "
            f"(largest is {biggest_vehicle:g}) — it can never be delivered.")

    lo, hi = TRAIN["n"]
    if not lo <= n <= hi:
        warnings.append(
            f"{n} orders is outside the training range {lo}–{hi}; the models "
            "still run but this measures generalisation, not in-distribution quality.")
    lo, hi = TRAIN["m"]
    if not lo <= m <= hi:
        warnings.append(f"{m} vehicles is outside the training range {lo}–{hi}.")
    if any(not TRAIN["capacity"][0] <= v["capacity"] <= TRAIN["capacity"][1] for v in vehs):
        warnings.append("Some capacities fall outside the trained range 20–41.")
    if any(not TRAIN["speed"][0] <= v["speed"] <= TRAIN["speed"][1] for v in vehs):
        warnings.append("Some speeds fall outside the trained range 0.5–1.0.")
    if any(not TRAIN["demand"][0] <= c["demand"] <= TRAIN["demand"][1] for c in custs):
        warnings.append("Some demands fall outside the trained range 1–9.")

    # vehicles reload at the depot, so this is about how many trips are implied
    if total_demand > sum(v["capacity"] for v in vehs):
        warnings.append(
            f"Total demand {total_demand:g} exceeds one full fleet load "
            f"({sum(v['capacity'] for v in vehs):g}); vehicles will need several trips.")

    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "n": n, "m": m, "total_demand": total_demand}
