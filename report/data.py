"""Every number that appears in the report, with its provenance.

Keeping the data here rather than inline in the prose means the tables, the
charts and the summary all read from one place, so they cannot drift apart.

Sources (all committed on the branches named):
  hcvrp_k_trained_test.log      k sweep, each model at its own k
  tanh_sweep_test.log           tanh arms a / b / d
  hcvrp_equal_budget.log        equal-budget sweep
  hcvrp_k{1,2,4,7}_parco.log    k training runs (epoch wall-clock)
  tanh_a_ctrl_fixed.log etc.    tanh training runs
  hcvrp_dynamic_encoding_parco.log
"""

import statistics as st

SETS = [(n, m) for n in (40, 60, 80, 100) for m in (3, 5, 7)]

# ---------------------------------------------------------------- k sweep --
# (cost, decoding steps) per test set, greedy, batch 128
K_TRAINED = {
    1: {(100, 3): (11.4836, 124.6), (100, 5): (6.9243, 122.0), (100, 7): (5.0461, 121.1),
        (40, 3): (5.5669, 50.2), (40, 5): (3.5573, 48.9), (40, 7): (2.8649, 46.9),
        (60, 3): (7.4667, 74.3), (60, 5): (4.6451, 73.0), (60, 7): (3.4813, 71.4),
        (80, 3): (9.5481, 99.6), (80, 5): (5.8043, 97.5), (80, 7): (4.2676, 96.0)},
    2: {(100, 3): (11.6097, 62.4), (100, 5): (6.9809, 61.4), (100, 7): (5.0946, 61.0),
        (40, 3): (5.7305, 25.4), (40, 5): (3.6439, 24.9), (40, 7): (2.9341, 24.6),
        (60, 3): (7.6026, 37.5), (60, 5): (4.7171, 36.9), (60, 7): (3.5362, 36.3),
        (80, 3): (9.6767, 50.1), (80, 5): (5.8700, 49.3), (80, 7): (4.3184, 48.5)},
    4: {(100, 3): (12.0446, 42.0), (100, 5): (7.2242, 31.0), (100, 7): (5.2467, 31.0),
        (40, 3): (6.0268, 17.4), (40, 5): (3.8704, 13.0), (40, 7): (2.9971, 13.0),
        (60, 3): (7.9545, 25.4), (60, 5): (4.9494, 19.1), (60, 7): (3.6722, 19.0),
        (80, 3): (10.0808, 33.9), (80, 5): (6.0962, 25.0), (80, 7): (4.4685, 25.0)},
    7: {(100, 3): (12.1107, 42.0), (100, 5): (7.4789, 25.0), (100, 7): (5.5868, 18.0),
        (40, 3): (5.9939, 17.1), (40, 5): (4.0316, 10.3), (40, 7): (3.2329, 7.9),
        (60, 3): (7.9547, 25.2), (60, 5): (5.1379, 15.2), (60, 7): (4.0116, 11.0),
        (80, 3): (10.0729, 33.8), (80, 5): (6.3291, 20.2), (80, 7): (4.8180, 14.5)},
}

# --------------------------------------------------------------- tanh arms --
TANH = {
    "a": {"label": "(a) fixed  10·tanh(z)", "lr": "1e-4", "epoch": "10:03", "data": {
        (100, 3): (11.7403, 97.10), (100, 5): (7.1387, 90.30), (100, 7): (5.2665, 86.20),
        (40, 3): (5.8300, 43.50), (40, 5): (3.8200, 39.40), (40, 7): (3.1336, 37.30),
        (60, 3): (7.6990, 61.90), (60, 5): (4.8685, 57.00), (60, 7): (3.7261, 52.70),
        (80, 3): (9.7786, 78.70), (80, 5): (6.0101, 74.00), (80, 7): (4.5059, 69.40)}},
    "b": {"label": "(b) scaled  10·tanh(z/10)", "lr": "1e-4", "epoch": "09:59", "data": {
        (100, 3): (11.7133, 88.20), (100, 5): (7.0926, 81.40), (100, 7): (5.2286, 77.80),
        (40, 3): (5.7714, 41.70), (40, 5): (3.7570, 37.80), (40, 7): (3.0617, 36.20),
        (60, 3): (7.6536, 58.30), (60, 5): (4.8287, 54.00), (60, 7): (3.6769, 49.40),
        (80, 3): (9.7331, 71.90), (80, 5): (5.9851, 70.50), (80, 7): (4.4598, 63.90)}},
    "d": {"label": "(d) scaled, lr 1e-3", "lr": "1e-3", "epoch": "04:43", "data": {
        (100, 3): (99.8228, 198.6), (100, 5): (98.0644, 198.6), (100, 7): (97.5217, 198.6),
        (40, 3): (41.7095, 79.0), (40, 5): (41.0873, 79.0), (40, 7): (41.4409, 79.0),
        (60, 3): (59.1061, 119.0), (60, 5): (57.7562, 119.0), (60, 7): (58.2656, 119.0),
        (80, 3): (80.3093, 159.0), (80, 5): (78.4996, 159.0), (80, 7): (78.4699, 159.0)}},
}
CONTROL = TANH["a"]["data"]          # stock PARCO = the control for everything

EPOCH_MIN = {"parallel": "10:03", 1: "11:51", 2: "08:28", 4: "05:51", 7: "05:40"}

# ------------------------------------------------------- equal-budget sweep --
# cost reachable within a budget, as a multiple of one greedy parallel rollout
EQUAL_BUDGET = {
    "mults": [1.3, 2.0, 4.0, 8.0, 32.0],
    "rows": {
        "parallel": [6.0513, 6.1258, 6.1258, 6.1258, 6.1258],
        "k1":       [5.8007, 5.8880, 5.8880, 5.8880, 5.8880],
        "k2":       [5.9187, 5.9769, 5.9769, 5.9769, 5.9769],
        "k4":       [6.1847, 6.2187, 6.2187, 6.2187, 6.2187],
        "k7":       [6.2562, 6.3963, 6.3963, 6.3963, 6.3963],
    },
    "sets_in_common": [5, 12, 12, 12, 12],
}
# mean cost over 12 sets at each best-of-n sample count
BEST_OF_N = {
    "n":        [1, 2, 3, 4, 6, 8, 12, 16, 24, 32],
    "parallel": [6.1258, 13.8132, 12.5294, 12.3498, 11.1926, 10.1700, 8.2204, 6.2033, 6.2820, 6.2083],
    "k1":       [5.8880, 13.1290, 11.9503, 11.8178, 10.7250, 9.7214, 7.8248, 5.9545, 5.9489, 5.8975],
    "k2":       [5.9769, 13.2836, 12.0962, 11.9546, 10.8477, 9.8738, 7.9867, 6.0638, 6.1244, 6.0588],
    "k4":       [6.2187, 14.3181, 12.9767, 12.7811, 11.5408, 10.5506, 8.5666, 6.3363, 6.6137, 6.5202],
    "k7":       [6.3963, 15.3962, 13.8854, 13.6026, 12.2157, 11.2431, 9.1503, 6.5225, 7.0990, 6.9857],
}
# best sampling result relative to that model's own greedy result
SAMPLING_VS_GREEDY = {"parallel": (+1.08, 1), "k1": (+0.09, 4), "k2": (+1.35, 0),
                      "k4": (+1.92, 0), "k7": (+2.02, 0)}

# budget a single greedy rollout costs, relative to parallel PARCO
GREEDY_BUDGET_MULT = {"parallel": 1.00, "k1": 1.34, "k2": 0.68, "k4": 0.38, "k7": 0.31}

# --------------------------------------------------------------------- CVRP --
CVRP = [("n50 m3", 3.779, 52.4, 0.150), ("n50 m5", 2.463, 50.0, 0.145),
        ("n50 m7", 2.190, 49.1, 0.143), ("n100 m3", 6.163, 96.5, 0.324),
        ("n100 m5", 3.829, 96.1, 0.278), ("n100 m7", 2.999, 95.1, 0.280),
        ("n200 m3 †", 28.487, 245.2, 0.746), ("n200 m5 †", 6.977, 186.7, 0.575),
        ("n200 m7 †", 4.898, 174.7, 0.549)]

# --------------------------------------------------------------- validation --
PAPER_VS_CKPT = [("n100 m3", 10.98, 10.977), ("n100 m5", 6.61, None), ("n100 m7", 4.80, None)]

VARIANCE_SHARE = [(2, 0.0), (3, 11.0), (4, 24.5)]       # avoidable variance, conflict map
ORDER_SHARE = [(1, 0.0), (2, 13.3), (3, 46.6)]          # avoidable variance, pick order at k


# ------------------------------------------------------------------ helpers --
def mean_cost(d):
    return st.mean(d[s][0] for s in SETS)


def mean_steps(d):
    return st.mean(d[s][1] for s in SETS)


def gap(d, ref=CONTROL):
    return 100 * st.mean((d[s][0] - ref[s][0]) / ref[s][0] for s in SETS)


def wins(d, ref=CONTROL):
    return sum(d[s][0] < ref[s][0] for s in SETS)


def gap_by_m(d, m, ref=CONTROL):
    sub = [(n, m) for n in (40, 60, 80, 100)]
    return 100 * st.mean((d[s][0] - ref[s][0]) / ref[s][0] for s in sub)


def headline():
    """The single table the executive summary is built from."""
    rows = [("Parallel PARCO (control)", mean_cost(CONTROL), 0.0, None,
             mean_steps(CONTROL), EPOCH_MIN["parallel"], "reference")]
    for k, verdict in ((1, "best quality"), (2, "dominates")):
        d = K_TRAINED[k]
        rows.append((f"k = {k}", mean_cost(d), gap(d), wins(d), mean_steps(d),
                     EPOCH_MIN[k], verdict))
    b = TANH["b"]["data"]
    rows.append(("Tanh scaled 10·tanh(z/10)", mean_cost(b), gap(b), wins(b),
                 mean_steps(b), TANH["b"]["epoch"], "small, free win"))
    for k, verdict in ((4, "speed point"), (7, "fastest")):
        d = K_TRAINED[k]
        rows.append((f"k = {k}", mean_cost(d), gap(d), wins(d), mean_steps(d),
                     EPOCH_MIN[k], verdict))
    dd = TANH["d"]["data"]
    rows.append(("Tanh scaled, lr 1e-3", mean_cost(dd), gap(dd), wins(dd),
                 None, TANH["d"]["epoch"], "diverged at ep. 22"))
    return rows


if __name__ == "__main__":
    print(f"{'method':30} {'cost':>9} {'gap':>8} {'wins':>6} {'passes':>8} {'epoch':>7}")
    for r in headline():
        g = "—" if r[2] is None else f"{r[2]:+.2f}%"
        w = "—" if r[3] is None else f"{r[3]}/12"
        p = "—" if r[4] is None else f"{r[4]:.1f}"
        print(f"{r[0]:30} {r[1]:9.4f} {g:>8} {w:>6} {p:>8} {r[5]:>7}")
