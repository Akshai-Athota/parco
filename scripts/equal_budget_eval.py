"""Equal-budget comparison of parallel PARCO against the k-parallel models.

Why this exists
---------------
The greedy table says k=1 (full sequential) beats parallel PARCO by 4.6% on
HCVRP. But a greedy k=1 rollout spends ~85 decoder passes against PARCO's ~66,
so part of that win could simply be bought with extra inference compute. This
script removes the confound by measuring every model on the same budget axis.

Budget accounting
-----------------
One decoder pass = one evaluation of the decoder head, producing the [B, M, A]
logits. This is the honest unit here because a k-parallel pass commits its k
pairs from a *single* logits tensor (see KParallelDecodingStrategy.step), so a
pass costs the same whatever k is. For best-of-n sampling all n rollouts of an
instance advance in lockstep, so

    passes per instance = (decoding steps) * (number of samples)

Both factors are measured, never assumed, so every point is auditable.

Rather than force a single matched point (which needs an awkward rounding of
samples per method), we sweep each model over several sample counts and report
cost against the budget actually consumed. "Equal budget" is then read off the
curve: for a budget B, a model's achievable cost is the best it reaches using
no more than B passes. That is what ``--budgets`` tabulates.

Usage
-----
    python scripts/equal_budget_eval.py --samples 2 4 8 16 32 --out results.csv
"""

import argparse
import csv
import os
import time
import warnings
from collections import defaultdict

import torch

from rl4co.data.utils import load_npz_to_tensordict
from rl4co.utils.ops import unbatchify

from parco.envs import HCVRPEnv
from parco.models import PARCORLModule
from parco.tasks.eval import get_dataloader

warnings.filterwarnings("ignore", category=FutureWarning)
torch.set_float32_matmul_precision("medium")

DEFAULT_RUNS_ROOT = "logs/train/runs/hcvrp_n100_m7"
# Stock parallel PARCO is the tanh control arm: plain fixed clipping, encoder
# attention untouched, trained on the same 6 GPUs with the same recipe as every
# k run. It is the baseline for this comparison. Note it was trained on a
# different branch than the k runs, so if the two sets of logs live in separate
# clones on the cluster, point --parallel_run at an absolute path.
DEFAULT_PARALLEL_RUN = "parco_tanh_fixed_g10_t1_attn0_lr0.0001"


def build_methods(runs_root, parallel_run, ks):
    """-> list of (name, run_dir, decode family, decode_k)."""

    def under(path):
        return path if os.path.isabs(path) else os.path.join(runs_root, path)

    methods = [("parallel", under(parallel_run), "plain", None)]
    for k in ks:
        methods.append((f"k{k}", under(f"parco_k{k}"), "kparallel", k))
    return methods


def resolve_checkpoint(run_dir):
    """Newest ``<run_dir>/<timestamp>/checkpoints/last.ckpt``, or None."""
    if not os.path.isdir(run_dir):
        return None
    cands = []
    for ts in os.listdir(run_dir):
        ckpt = os.path.join(run_dir, ts, "checkpoints", "last.ckpt")
        if os.path.exists(ckpt):
            cands.append(ckpt)
    if not cands:
        return None
    return max(cands, key=os.path.getmtime)


def evaluate(
    policy, env, dataset, device, decode_type, decode_k, n_samples, instances_per_batch
):
    """Return (best-of-n mean cost, mean decoding steps, wall seconds).

    ``instances_per_batch`` is deliberately held constant across every method
    and every sample count. The decoding loop runs ``while not done.all()``, so
    the reported step count is the MAX trajectory length over the batch and
    therefore grows with the number of instances in it. Measuring every
    configuration at the same batch width is what keeps the budget axis
    comparable. Memory scales as instances_per_batch * n_samples, so this also
    bounds the peak at the largest sample count.
    """
    td_test = load_npz_to_tensordict(dataset)
    dataloader = get_dataloader(td_test, batch_size=instances_per_batch)

    extra = {"decode_k": decode_k} if decode_k is not None else {}
    costs, steps = [], []
    t0 = time.time()
    # mirror test.py: autocast on CUDA, so costs reproduce the published table
    autocast_ctx = (
        torch.autocast("cuda") if device.type == "cuda" else torch.inference_mode()
    )
    with autocast_ctx:
        with torch.inference_mode():
            for td_batch in dataloader:
                td_reset = env.reset(td_batch).to(device)
                out = policy(
                    td_reset,
                    env,
                    decode_type=decode_type,
                    num_samples=n_samples,
                    return_actions=False,
                    **extra,
                )
                reward = out["reward"]
                if "sampling" in decode_type:
                    # batchify repeats sample-major; unbatchify -> [B, n_samples]
                    cost = -unbatchify(reward, n_samples).max(dim=-1)[0]
                else:
                    cost = -reward
                costs.extend(cost.flatten().float().tolist())
                steps.append(float(out["steps"]))
    wall = time.time() - t0
    return sum(costs) / len(costs), sum(steps) / len(steps), wall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", default="hcvrp")
    ap.add_argument(
        "--samples",
        type=int,
        nargs="+",
        default=[2, 4, 8, 16, 32],
        help="Sampling rollouts per instance. Greedy (1 pass) is always added.",
    )
    ap.add_argument(
        "--budgets",
        type=float,
        nargs="+",
        default=[0.5, 0.75, 1.0, 1.3, 2.0, 4.0, 8.0, 16.0, 32.0],
        help="Budget levels for the final table, as multiples of ONE greedy "
        "rollout of the reference model on that dataset. 1.3x is where "
        "parallel PARCO matches a greedy k=1 rollout.",
    )
    ap.add_argument(
        "--reference",
        default="parallel",
        help="Method whose single greedy rollout defines budget 1.0x.",
    )
    ap.add_argument(
        "--instances_per_batch",
        type=int,
        default=16,
        help="Instances per batch, held constant for every method and sample "
        "count so the measured step counts stay comparable. Peak memory "
        "scales as instances_per_batch * max(--samples).",
    )
    ap.add_argument(
        "--runs_root",
        default=DEFAULT_RUNS_ROOT,
        help="Directory holding the per-run folders.",
    )
    ap.add_argument(
        "--parallel_run",
        default=DEFAULT_PARALLEL_RUN,
        help="Run folder for stock parallel PARCO (the tanh control arm), "
        "relative to --runs_root, or an absolute path if that checkpoint "
        "lives in a different clone.",
    )
    ap.add_argument(
        "--ks",
        type=int,
        nargs="+",
        default=[1, 2, 4, 7],
        help="Which k-parallel models to include; expects parco_k<K> under "
        "--runs_root. Add 3 5 6 once those runs finish.",
    )
    ap.add_argument("--datasets", nargs="+", default=None)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", default="equal_budget_results.csv")
    opts = ap.parse_args()

    device = (
        torch.device("cuda:0")
        if "cuda" in opts.device and torch.cuda.is_available()
        else torch.device("cpu")
    )

    if opts.datasets is None:
        data_dir = f"./data/{opts.problem}"
        if not os.path.isdir(data_dir):
            raise SystemExit(
                f"no test data at {data_dir}. Run test.py once to let it "
                "download from HuggingFace, or pass --datasets explicitly."
            )
        paths = [f"{data_dir}/{f}" for f in os.listdir(data_dir) if "sol" not in f]
    else:
        paths = list(opts.datasets)
    paths = sorted(paths)

    env = HCVRPEnv()
    rows = []

    # Resolve every checkpoint up front: an 8-hour sweep should fail in the
    # first second if a path is wrong, not after the first model is done.
    methods = build_methods(opts.runs_root, opts.parallel_run, opts.ks)
    missing = [n for n, d, _, _ in methods if resolve_checkpoint(d) is None]
    if missing:
        print(f"[warn] no checkpoint found for: {', '.join(missing)}")
        for n, d, _, _ in methods:
            if n in missing:
                print(f"         {n:10} looked under {d}")
        if "parallel" in missing:
            raise SystemExit(
                "the parallel baseline is missing, so no matched-budget table "
                "can be built. It is the tanh control arm, which was trained "
                "on a different branch -- point --parallel_run at its run "
                "folder (an absolute path is fine)."
            )
    if len(missing) == len(methods):
        raise SystemExit("no checkpoints resolved at all; check --runs_root")

    # Written incrementally: this sweep runs for hours, and a single OOM late in
    # it must not take every earlier measurement with it.
    fields = [
        "method", "dataset", "decode_type", "samples",
        "cost", "steps", "passes", "wall_s",
    ]
    csv_fh = open(opts.out, "w", newline="")
    writer = csv.DictWriter(csv_fh, fieldnames=fields)
    writer.writeheader()
    csv_fh.flush()

    try:
        for name, run_dir, family, decode_k in methods:
            ckpt = resolve_checkpoint(run_dir)
            if ckpt is None:
                print(f"[{name}] no checkpoint under {run_dir}, skipping")
                continue
            print(f"\n{'=' * 70}\n[{name}] {ckpt}\n{'=' * 70}", flush=True)
            model = PARCORLModule.load_from_checkpoint(
                ckpt, map_location="cpu", strict=False
            )
            policy = model.policy.to(device).eval()

            greedy_type = "kparallel_greedy" if family == "kparallel" else "greedy"
            sampling_type = (
                "kparallel_sampling" if family == "kparallel" else "sampling"
            )

            for dataset in paths:
                tag = os.path.basename(dataset).replace(".npz", "")
                plan = [(greedy_type, 1)] + [(sampling_type, n) for n in opts.samples]
                for decode_type, n in plan:
                    try:
                        cost, steps, wall = evaluate(
                            policy, env, dataset, device, decode_type, decode_k,
                            n, opts.instances_per_batch,
                        )
                    except torch.cuda.OutOfMemoryError:
                        print(
                            f"  {tag:12} {decode_type:19} n={n:<3} OOM, skipped "
                            f"(lower --instances_per_batch to reach this point)",
                            flush=True,
                        )
                        torch.cuda.empty_cache()
                        continue
                    except Exception as exc:  # keep the sweep alive
                        print(
                            f"  {tag:12} {decode_type:19} n={n:<3} FAILED: "
                            f"{type(exc).__name__}: {exc}",
                            flush=True,
                        )
                        continue

                    row = dict(
                        method=name, dataset=tag, decode_type=decode_type,
                        samples=n, cost=round(cost, 4), steps=round(steps, 2),
                        passes=round(steps * n, 2), wall_s=round(wall, 2),
                    )
                    rows.append(row)
                    writer.writerow(row)
                    csv_fh.flush()
                    print(
                        f"  {tag:12} {decode_type:19} n={n:<3} "
                        f"cost={cost:8.4f}  steps={steps:7.2f}  "
                        f"passes={steps * n:8.1f}  {wall:6.1f}s",
                        flush=True,
                    )
            del model, policy
            if device.type == "cuda":
                torch.cuda.empty_cache()
    finally:
        csv_fh.close()

    if not rows:
        print("\nno results: none of the checkpoints could be resolved")
        return

    print(f"\nwrote {opts.out} ({len(rows)} rows)")
    report(rows, opts.budgets, reference=opts.reference)


def report(rows, budget_mults, reference="parallel"):
    """Cost reachable within each budget, averaged over the datasets.

    Budget is relative: 1.0x means "the decoder passes parallel PARCO spends on
    one greedy rollout of this dataset". Absolute pass counts are not
    comparable across N (n40 needs ~43 passes, n100 ~97), so the relative unit
    is what makes averaging over datasets meaningful -- and it is the direct
    answer to "give the parallel model the same budget as the sequential one".
    """
    # (method, dataset) -> list of (passes, cost)
    curve = defaultdict(list)
    for r in rows:
        curve[(r["method"], r["dataset"])].append((r["passes"], r["cost"]))

    methods = sorted({r["method"] for r in rows}, key=lambda m: (m != reference, m))
    datasets = sorted({r["dataset"] for r in rows})

    # per-dataset budget unit: the reference model's single greedy rollout
    unit = {}
    for d in datasets:
        g = [
            r["passes"]
            for r in rows
            if r["method"] == reference and r["dataset"] == d and r["samples"] == 1
        ]
        if g:
            unit[d] = g[0]
    if not unit:
        print(f"\n[report] no greedy row for reference '{reference}', skipping table")
        return

    def cost_within(method, dataset, budget):
        """Best cost reachable using no more than `budget` passes, else None."""
        pts = [c for p, c in curve[(method, dataset)] if p <= budget]
        return min(pts) if pts else None

    print("\n" + "=" * 78)
    print("COST AT MATCHED BUDGET")
    print(f"budget 1.0x = one greedy rollout of '{reference}' on that dataset")
    print("each cell averages only the datasets where EVERY method fits the budget")
    print("=" * 78)
    print(
        f"{'budget':>8} "
        + " ".join(f"{m:>10}" for m in methods)
        + f" {'sets':>5}   winner"
    )
    for mult in budget_mults:
        common = [
            d
            for d in datasets
            if d in unit
            and all(cost_within(m, d, mult * unit[d]) is not None for m in methods)
        ]
        if not common:
            cells = " ".join(f"{'-':>10}" for _ in methods)
            print(f"{mult:7.2f}x {cells} {0:5d}   (no method fits)")
            continue
        vals = {
            m: sum(cost_within(m, d, mult * unit[d]) for d in common) / len(common)
            for m in methods
        }
        best = min(vals, key=lambda m: vals[m])
        cells = " ".join(f"{vals[m]:10.4f}" for m in methods)
        note = "" if len(common) == len(datasets) else "  (subset)"
        print(f"{mult:7.2f}x {cells} {len(common):5d}   {best}{note}")

    print("\nper-dataset winner by budget (how many of the test sets each method wins)")
    for mult in budget_mults:
        tally = defaultdict(int)
        for d in datasets:
            if d not in unit:
                continue
            vals = {m: cost_within(m, d, mult * unit[d]) for m in methods}
            if any(v is None for v in vals.values()):
                continue
            tally[min(vals, key=lambda m: vals[m])] += 1
        if tally:
            summary = ", ".join(f"{m}:{c}" for m, c in sorted(tally.items()))
            print(f"  {mult:6.2f}x  {summary}")


if __name__ == "__main__":
    main()
