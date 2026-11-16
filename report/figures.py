"""Charts for the report. Each function writes one PNG and returns its path."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt            # noqa: E402
import numpy as np                         # noqa: E402

import data as D                           # noqa: E402

NAVY, ORANGE, TEAL, GOLD, PURPLE, GREY = (
    "#12304A", "#E2561F", "#12927A", "#D9A21B", "#7E5AA8", "#8296A6")
MUTED = "#5B7085"
DPI = 200

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": "#C9D4DD", "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": "#E8EEF2", "grid.linewidth": .8,
    "axes.axisbelow": True, "figure.facecolor": "white",
})


def _finish(fig, ax_or_axes, out):
    for ax in (ax_or_axes if isinstance(ax_or_axes, (list, tuple, np.ndarray)) else [ax_or_axes]):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return out


def pareto(outdir):
    out = os.path.join(outdir, "pareto.png")
    fig, ax = plt.subplots(figsize=(6.4, 3.5))

    pts = [("Parallel\nPARCO", D.mean_steps(D.CONTROL), D.mean_cost(D.CONTROL), NAVY)]
    for k, col in ((1, ORANGE), (2, TEAL), (4, PURPLE), (7, GREY)):
        d = D.K_TRAINED[k]
        pts.append((f"k = {k}", D.mean_steps(d), D.mean_cost(d), col))

    kx = [p[1] for p in pts[1:]], [p[2] for p in pts[1:]]
    ax.plot(kx[0], kx[1], "-", color="#B9C6D1", lw=1.4, zorder=1)
    for label, x, y, col in pts:
        ax.scatter([x], [y], s=130, color=col, zorder=3, edgecolor="white", lw=1.6)
        ax.annotate(label, (x, y), textcoords="offset points",
                    xytext=(0, 14), ha="center", fontsize=8.5,
                    color=col, fontweight="bold")

    ctrl = D.mean_cost(D.CONTROL)
    ax.axhline(ctrl, color=NAVY, ls=":", lw=1.1, zorder=0)
    ax.annotate("control", (97, ctrl), fontsize=8, color=NAVY, va="bottom")

    ax.set_xlabel("decoder passes per instance  (lower = faster)")
    ax.set_ylabel("mean cost over 12 test sets\n(lower = better)")
    ax.set_xlim(8, 100)
    ax.set_ylim(5.75, 6.55)
    return _finish(fig, ax, out)


def m_scaling(outdir):
    out = os.path.join(outdir, "m_scaling.png")
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    ms = [3, 5, 7]
    width = .2
    for i, (k, col) in enumerate(((1, ORANGE), (2, TEAL), (4, PURPLE), (7, GREY))):
        vals = [D.gap_by_m(D.K_TRAINED[k], m) for m in ms]
        xs = np.arange(len(ms)) + (i - 1.5) * width
        ax.bar(xs, vals, width, color=col, label=f"k = {k}")
        for x, v in zip(xs, vals):
            ax.annotate(f"{v:+.1f}", (x, v), ha="center", fontsize=7.2, color=MUTED,
                        va="bottom" if v > 0 else "top",
                        xytext=(0, 2 if v > 0 else -3), textcoords="offset points")
    ax.axhline(0, color=NAVY, lw=1.1)
    ax.set_xticks(range(len(ms)))
    ax.set_xticklabels([f"M = {m}" for m in ms])
    ax.set_ylabel("cost gap vs parallel PARCO (%)")
    ax.set_ylim(-8, 8)
    ax.legend(frameon=False, ncol=4, fontsize=8.5, loc="upper left")
    return _finish(fig, ax, out)


def tanh_curves(outdir):
    out = os.path.join(outdir, "tanh_curves.png")
    z = np.linspace(-12, 12, 600)
    fixed, scaled = 10 * np.tanh(z), 10 * np.tanh(z / 10)
    dfixed, dscaled = 10 / np.cosh(z) ** 2, 1 / np.cosh(z / 10) ** 2

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7))
    axes[0].plot(z, fixed, color=GOLD, lw=2.2, label=r"$10\tanh(z)$  (PARCO)")
    axes[0].plot(z, scaled, color=TEAL, lw=2.2, label=r"$10\tanh(z/10)$  (scaled)")
    axes[0].plot(z, z, color="#C3CED7", lw=1.1, ls="--", label="identity")
    axes[0].set_ylim(-12, 12)
    axes[0].set_title(r"$\varphi(z)$", fontsize=9.5, color=NAVY)
    axes[0].legend(frameon=False, fontsize=7.4, loc="upper left")

    axes[1].plot(z, dfixed, color=GOLD, lw=2.2)
    axes[1].plot(z, dscaled, color=TEAL, lw=2.2)
    axes[1].axhline(1, color="#C3CED7", lw=1.1, ls="--")
    axes[1].set_title(r"slope $\varphi'(z)=(g/\tau)\,\mathrm{sech}^2(z/\tau)$",
                      fontsize=9.5, color=NAVY)
    axes[1].annotate("gain 10 at the origin", (0, 10), fontsize=7.6, color=GOLD,
                     xytext=(2.0, 8.4), textcoords="data")
    axes[1].annotate("gain 1", (0, 1), fontsize=7.6, color=TEAL,
                     xytext=(4.5, 1.9), textcoords="data")
    for ax in axes:
        ax.set_xlabel("logit  z")
    return _finish(fig, axes, out)


def budget(outdir):
    out = os.path.join(outdir, "budget.png")
    fig, ax = plt.subplots(figsize=(6.4, 3.1))
    mults = D.EQUAL_BUDGET["mults"]
    styles = {"parallel": (NAVY, "Parallel PARCO"), "k1": (ORANGE, "k = 1"),
              "k2": (TEAL, "k = 2"), "k4": (PURPLE, "k = 4"), "k7": (GREY, "k = 7")}
    for key, (col, lab) in styles.items():
        ax.plot(mults, D.EQUAL_BUDGET["rows"][key], "o-", color=col, lw=1.9,
                ms=5, label=lab)
    ax.set_xscale("log")
    ax.set_xticks(mults)
    ax.set_xticklabels([f"{m:g}×" for m in mults])
    ax.set_xlabel("inference budget, as a multiple of one greedy parallel-PARCO rollout")
    ax.set_ylabel("best cost reachable\nwithin the budget")
    ax.legend(frameon=False, ncol=5, fontsize=8, loc="upper center",
              bbox_to_anchor=(.5, 1.18))
    return _finish(fig, ax, out)


def best_of_n(outdir):
    out = os.path.join(outdir, "best_of_n.png")
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    ns = D.BEST_OF_N["n"]
    for key, col, lab in (("parallel", NAVY, "Parallel PARCO"), ("k1", ORANGE, "k = 1"),
                          ("k7", GREY, "k = 7")):
        ax.plot(ns, D.BEST_OF_N[key], "o-", color=col, lw=1.8, ms=4, label=lab)
    ax.axhline(D.BEST_OF_N["parallel"][0], color=NAVY, ls=":", lw=1.1)
    ax.annotate("parallel PARCO, greedy", (20, D.BEST_OF_N["parallel"][0] + 1.0),
                fontsize=7.8, color=NAVY)
    ax.set_xlabel("best-of-n sampling rollouts per instance  (n = 1 is greedy)")
    ax.set_ylabel("mean cost over 12 test sets")
    ax.legend(frameon=False, fontsize=8.2, loc="upper right")
    return _finish(fig, ax, out)


ALL = [pareto, m_scaling, tanh_curves, budget, best_of_n]


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    return {fn.__name__: fn(outdir) for fn in ALL}


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "report/_figs"
    for name, path in build(out).items():
        print(f"  {name:14} {path}")
