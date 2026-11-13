"""Check the demo's model path before you rely on it in front of an audience.

Run this once on whatever machine will host the demo:

    python demo/selftest.py                 # every checkpoint it can find
    python demo/selftest.py --methods k1 k2

For each method it solves one small instance and verifies three things:

  1. the policy runs at all and returns actions
  2. the routes we reconstruct reproduce the environment's own reward -- if these
     disagree, the picture on screen does not match the score in the table
  3. the solution is actually feasible: every order served exactly once and no
     vehicle over capacity

Exit code is non-zero if any check fails, so it also works in a script.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenarios                                           # noqa: E402
from backends import DEFAULT_RUNS_ROOT, METHODS, TorchBackend, resolve_runs_root  # noqa: E402
from routes import validity                                # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT)
    ap.add_argument("--methods", nargs="+", default=None)
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--m", type=int, default=4)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--device", default="cpu")
    opts = ap.parse_args()

    root = resolve_runs_root(opts.runs_root)
    print(f"runs root : {root}")
    if not os.path.isdir(root):
        print("  !! that directory does not exist")
        return 2

    try:
        backend = TorchBackend(opts.runs_root, opts.device)
    except Exception as exc:
        print(f"  !! could not create the torch backend: {type(exc).__name__}: {exc}")
        print("     the demo will still run with --mock (heuristic only)")
        return 2

    found = backend.available()
    print(f"checkpoints found: {', '.join(found) if found else 'NONE'}")
    for key in METHODS:
        if key not in found:
            print(f"  - {key:9} missing  (looked for {METHODS[key]['run']})")
    if not found:
        return 2

    todo = [m for m in (opts.methods or found) if m in found]
    sc = scenarios.generate(n=opts.n, m=opts.m, layout="clusters", seed=opts.seed)
    print(f"\ninstance  : {opts.n} orders, {opts.m} vehicles, seed {opts.seed}\n")

    header = f"{'method':10} {'objective':>10} {'env':>10} {'steps':>6} {'ms':>7}  checks"
    print(header)
    print("-" * len(header))

    failures = 0
    for key in todo:
        try:
            plan = backend.plan(sc, [key])[key]
        except Exception as exc:
            print(f"{key:10} FAILED: {type(exc).__name__}: {exc}")
            failures += 1
            continue

        v = validity(plan, len(sc["customers"]))
        problems = []
        if plan.note:
            problems.append("reward mismatch")
        if not v["all_served"]:
            problems.append(f"{len(v['missing'])} unserved")
        if v["duplicates"]:
            problems.append(f"{v['duplicates']} duplicate visits")
        if v["capacity_violations"]:
            problems.append(f"{len(v['capacity_violations'])} over capacity")

        status = "ok" if not problems else "; ".join(problems)
        # plan.note carries the environment's value when they disagree
        print(f"{key:10} {plan.objective:10.4f} {'=' if not plan.note else '≠':>10} "
              f"{plan.steps:6d} {plan.elapsed_ms:7.0f}  {status}")
        if plan.note:
            print(f"           {plan.note}")
        if problems:
            failures += 1

    print()
    if failures:
        print(f"{failures} of {len(todo)} method(s) failed — do not demo until fixed")
        return 1
    print(f"all {len(todo)} method(s) passed; the demo is safe to run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
