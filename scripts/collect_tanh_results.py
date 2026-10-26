"""Summarise the tanh sweep: one row per arm, mean cost over the 12 test sets.

    python scripts/collect_tanh_results.py [tanh_sweep_test.log]
"""
import re
import sys

RUN = re.compile(r"\[run\] (parco_tanh_\S+)")
COST = re.compile(r"Average cost:\s*([0-9.]+)")
DATA = re.compile(r"Loading \./data/\w+/(n\d+_m\d+)")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "tanh_sweep_test.log"
    run, dataset, rows = None, None, []
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.replace("\r", "")
        m = RUN.search(line)
        if m:
            run = m.group(1)
        d = DATA.search(line)
        if d:
            dataset = d.group(1)
        c = COST.search(line)
        if c and run and dataset:
            rows.append((run, dataset, float(c.group(1))))
            dataset = None
    if not rows:
        print("No results parsed from", path)
        return

    runs = sorted({r for r, _, _ in rows})
    base = [r for r in runs if "_fixed_" in r]
    base_mean = None
    if base:
        sub = [c for r, _, c in rows if r == base[0]]
        base_mean = sum(sub) / len(sub)

    print(f"{'arm':58} {'sets':>5} {'mean cost':>10} {'vs control':>11}")
    for r in runs:
        sub = [c for rr, _, c in rows if rr == r]
        mean = sum(sub) / len(sub)
        gap = "" if base_mean is None else f"{100*(mean-base_mean)/base_mean:+10.2f}%"
        print(f"{r:58} {len(sub):>5} {mean:10.4f} {gap:>11}")
    if base_mean is not None:
        print(f"\ncontrol = {base[0]}  (mean {base_mean:.4f})")
    print("negative = better than the control")


if __name__ == "__main__":
    main()
