"""Turn results/*.csv into figures/*.png and results/summary.md."""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(__file__)
RES = os.path.join(HERE, "..", "results")
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)

C = {"reactive": "#D55E00", "stc": "#0072B2", "central": "#009E73"}
LABEL = {"reactive": "Reactive stop-and-wait", "stc": "STC (decentralized)",
         "central": "Central prioritized planner"}
HCOL = {2: "#D55E00", 4: "#E69F00", 8: "#56B4E9", 12: "#0072B2"}

def wilson(k, n, z=1.96):
    """95% Wilson score interval for a proportion k/n (in percent)."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return 100 * max(0, c - h), 100 * min(1, c + h)


plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 130})


def methods_fig(df):
    order = ["crossing", "corridor", "corridor_hard", "open_grid", "mixed_city"]
    names = ["crossing", "corridor\n(2+2)", "corridor\n(3+3, hard)", "open grid", "mixed\ncity"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    w = 0.26
    for k, m in enumerate(["reactive", "stc", "central"]):
        s = [df[(df.scenario == sc) & (df["mode"] == m)].success.mean() * 100 for sc in order]
        d = [df[(df.scenario == sc) & (df["mode"] == m) & (df.arrived == df.n_agents)]
             .mean_delay.mean() for sc in order]
        xs = [i + (k - 1) * w for i in range(len(order))]
        a1.bar(xs, s, w, color=C[m], label=LABEL[m])
        a2.bar(xs, d, w, color=C[m], label=LABEL[m])
    for a in (a1, a2):
        a.set_xticks(range(len(order)))
        a.set_xticklabels(names, fontsize=8.5)
    a1.set_ylabel("runs: all arrived, zero collisions (%)")
    a1.set_ylim(0, 105)
    a2.set_ylabel("mean delay vs. free-space shortest path (ticks)")
    a1.set_title("Safe completion (no packet loss)")
    a2.set_title("Cost of coordination")
    h, l = a1.get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=9, loc="upper center", ncol=3)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(os.path.join(FIG, "fig1_methods.png"))
    plt.close(fig)


def sweep_fig(df):
    scen = ["crossing", "open_grid", "mixed_city"]
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.4), sharex=True)
    for j, sc in enumerate(scen):
        sub = df[df.scenario == sc]
        for h in sorted(sub.horizon.unique()):
            g = sub[sub.horizon == h].groupby("loss")
            xs = g.collision_free.mean().index * 100
            axes[0, j].plot(xs, g.collision_free.mean().values * 100, "-o", ms=4,
                            color=HCOL.get(h, "k"), label=f"H = {h}")
            ci = [wilson(k, n) for k, n in zip(g.collision_free.sum(), g.collision_free.count())]
            axes[0, j].fill_between(xs, [c[0] for c in ci], [c[1] for c in ci],
                                    color=HCOL.get(h, "k"), alpha=0.10, lw=0)
            ok = sub[(sub.horizon == h) & (sub.arrived == sub.n_agents)].groupby("loss")
            axes[1, j].plot(ok.mean_delay.mean().index * 100, ok.mean_delay.mean().values,
                            "-o", ms=4, color=HCOL.get(h, "k"), label=f"H = {h}")
        axes[0, j].set_title(sc.replace("_", " "))
        axes[1, j].set_xlabel("packet loss per link per tick (%)")
        axes[0, j].set_ylim(-3, 103)
    axes[0, 0].set_ylabel("collision-free runs (%)")
    axes[1, 0].set_ylabel("mean delay (ticks)")
    axes[0, 0].legend(frameon=False, title="corridor lookahead")
    fig.suptitle("Robustness to packet loss (30 seeds per point; bands = 95% Wilson intervals)",
                 y=1.0, fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_loss_sweep.png"))
    plt.close(fig)


def ablation_fig(df):
    scen = ["crossing", "open_grid", "mixed_city"]
    variants = [(1, 1, "full protocol"), (0, 1, "no announce-then-act"),
                (1, 0, "no sensing stop"), (0, 0, "neither")]
    cols = ["#0072B2", "#E69F00", "#009E73", "#D55E00"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, p in zip(axes, (0.0, 0.3)):
        for k, (a, s, name) in enumerate(variants):
            vals = [df[(df.scenario == sc) & (df.loss == p) & (df.announce_first == a)
                       & (df.sensing == s)].collision_free.mean() * 100 for sc in scen]
            ax.bar([i + (k - 1.5) * 0.2 for i in range(3)], vals, 0.2, color=cols[k], label=name)
            for i, sc in enumerate(scen):
                sel = df[(df.scenario == sc) & (df.loss == p) & (df.announce_first == a)
                         & (df.sensing == s)].collision_free
                lo, hi = wilson(sel.sum(), len(sel))
                ax.plot([i + (k - 1.5) * 0.2] * 2, [lo, hi], color="black", lw=0.8)
        ax.set_xticks(range(3))
        ax.set_xticklabels([s.replace("_", " ") for s in scen])
        ax.set_title(f"packet loss {int(p * 100)}%  (H = 12; bars = 95% Wilson intervals)", fontsize=10)
    axes[0].set_ylabel("collision-free runs (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=9, loc="upper center", ncol=4)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(os.path.join(FIG, "fig3_ablation.png"))
    plt.close(fig)


def summary(m, s, a):
    lines = ["# Benchmark summary (auto-generated)\n"]
    lines.append("## Methods, no packet loss (30 seeds per cell)\n")
    t = (m.groupby(["scenario", "mode"])
         .agg(success=("success", "mean"), collision_free=("collision_free", "mean"),
              mean_delay=("mean_delay", "mean"), replans=("replans", "mean"),
              msgs=("messages_sent", "mean")).round(3).reset_index())
    lines.append(t.to_markdown(index=False))
    lines.append("\n## Loss sweep: collision-free rate (%), by scenario / horizon / loss\n")
    p = (s.groupby(["scenario", "horizon", "loss"]).collision_free.mean() * 100).round(1)
    lines.append(p.unstack("loss").to_markdown())
    lines.append("\n## Loss sweep: all-arrived-and-safe rate (%)\n")
    p = (s.groupby(["scenario", "horizon", "loss"]).success.mean() * 100).round(1)
    lines.append(p.unstack("loss").to_markdown())
    lines.append("\n## Ablation (H=12): collision-free rate (%)\n")
    p = (a.groupby(["scenario", "loss", "announce_first", "sensing"]).collision_free.mean() * 100).round(1)
    lines.append(p.to_frame("collision_free_%").reset_index().to_markdown(index=False))
    open(os.path.join(RES, "summary.md"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    m = pd.read_csv(os.path.join(RES, "methods.csv"))
    s = pd.read_csv(os.path.join(RES, "loss_sweep.csv"))
    a = pd.read_csv(os.path.join(RES, "ablation.csv"))
    methods_fig(m)
    sweep_fig(s)
    ablation_fig(a)
    try:
        summary(m, s, a)
    except ImportError:                      # to_markdown needs `tabulate`
        print("tabulate not installed: skipped summary.md")
    print("figures written to", os.path.relpath(FIG))
