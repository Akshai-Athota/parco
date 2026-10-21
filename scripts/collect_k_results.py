"""Collect the k-parallel results into one table for the Pareto plot.

Usage, from the repository root after the test jobs have finished:

    python scripts/collect_k_results.py                  # reads hcvrp_k*_parco_test.log
    python scripts/collect_k_results.py hcvrp_k_sweep_test.log   # the zero-shot sweep

Prints one row per (k, test set) plus a per-k mean of cost and decoding steps,
which is what you plot as the speed/quality front.
"""

import glob
import os
import re
import sys

COST = re.compile(r"Average cost:\s*([0-9.]+)")
STEPS = re.compile(r"Average eval steps:\s*([0-9.]+)")
TIME = re.compile(r"Per step inference time:\s*([0-9.]+)")
DATA = re.compile(r"Loading \./data/\w+/(n\d+_m\d+)")
KTAG = re.compile(r"\[k = (\d+)\]")
WARMUP = "n100_m3"  # first dataset of every run: its timing includes GPU warm-up


def parse(path):
    """Yield (k, dataset, cost, steps, time) from a test log."""
    k = None
    m = re.search(r"hcvrp_k(\d+)_parco_test", os.path.basename(path))
    if m:
        k = int(m.group(1))
    dataset = None
    cost = steps = None
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.replace("\r", "")
        tag = KTAG.search(line)
        if tag:
            k = int(tag.group(1))
        d = DATA.search(line)
        if d:
            dataset, cost, steps, t = d.group(1), None, None, None
        c = COST.search(line)
        if c:
            cost = float(c.group(1))
        tm = TIME.search(line)
        if tm:
            t = float(tm.group(1))
        s = STEPS.search(line)
        if s and dataset is not None and cost is not None:
            yield k, dataset, cost, float(s.group(1)), t


def main():
    paths = sys.argv[1:] or sorted(glob.glob("hcvrp_k*_parco_test.log"))
    if not paths:
        print("No test logs found. Expected hcvrp_k<N>_parco_test.log in this directory.")
        return
    rows = [r for p in paths for r in parse(p)]
    if not rows:
        print("No results parsed from:", ", ".join(paths))
        return

    print(f"{'k':>3} {'test set':>10} {'cost':>9} {'steps':>8} {'time/batch':>11}")
    for k, d, c, s, t in sorted(rows, key=lambda r: (r[0] if r[0] is not None else 0, r[1])):
        ts = "        -" if t is None else f"{t:9.3f}s"
        print(f"{k if k is not None else '?':>3} {d:>10} {c:9.4f} {s:8.1f} {ts:>11}")

    print(f"\n{'k':>3} {'mean cost':>11} {'mean steps':>11} {'mean time/batch':>16}  (warm-up set excluded from time)")
    for k in sorted({r[0] for r in rows if r[0] is not None}):
        sub = [r for r in rows if r[0] == k]
        cost = sum(r[2] for r in sub) / len(sub)
        steps = sum(r[3] for r in sub) / len(sub)
        times = [r[4] for r in sub if r[4] is not None and WARMUP not in r[1]]
        tm = sum(times) / len(times) if times else float("nan")
        print(f"{k:>3} {cost:11.4f} {steps:11.1f} {tm:15.3f}s")
    print("\nPlot mean steps (x) against mean cost (y) to get the Pareto front.")


if __name__ == "__main__":
    main()
