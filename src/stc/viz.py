"""Matplotlib renderer: top-down animation of agents and their corridors."""
from __future__ import annotations

from typing import Sequence

from .agent import AgentSpec
from .sim import Result
from .world import AIR, World

PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9",
           "#F0E442", "#7A7A7A"]


def render_gif(world: World, specs: Sequence[AgentSpec], result: Result,
               path: str, fps: int = 5, title: str = "", dpi: int = 70) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.patches import Rectangle

    n = len(specs)
    t_max = max(t for tr in result.traj.values() for t, _ in tr)
    pos_at = {i: {t: c for t, c in result.traj[i]} for i in range(n)}
    arrival = {i: result.traj[i][-1][0] for i in range(n)}
    colors = [PALETTE[i % len(PALETTE)] for i in range(n)]

    fig, ax = plt.subplots(figsize=(6.4, 6.9))
    ax.set_xlim(-0.5, world.width - 0.5)
    ax.set_ylim(world.height - 0.5, -0.5)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#F7F7F5")
    for x, y in {(b[0], b[1]) for b in world.blocked}:
        ax.add_patch(Rectangle((x - 0.5, y - 0.5), 1, 1, color="#B8B8B2", lw=0))
    for i, s in enumerate(specs):
        ax.plot(s.goal[0], s.goal[1], marker="X", ms=7, color=colors[i],
                mec="white", mew=0.8, zorder=2)

    dots, wins, trails = [], [], []
    for i, s in enumerate(specs):
        marker = "^" if s.kind == AIR else "s"
        (d,) = ax.plot([], [], marker=marker, ms=11 if s.kind == AIR else 9,
                       color=colors[i], mec="black", mew=0.8, zorder=5)
        (w,) = ax.plot([], [], "-", lw=4, color=colors[i], alpha=0.30,
                       solid_capstyle="round", zorder=3)
        (tr,) = ax.plot([], [], "-", lw=1, color=colors[i], alpha=0.8, zorder=4)
        dots.append(d), wins.append(w), trails.append(tr)
    head = ax.set_title("", fontsize=11, loc="left")
    foot = fig.text(0.5, 0.015,
                    "square = ground vehicle   triangle = drone   X = goal   "
                    "faint band = reserved corridor",
                    ha="center", fontsize=8, color="#444")

    def frame(t):
        coll = sum(1 for tt, _ in result.collision_log if tt <= t)
        arrived = sum(1 for i in range(n) if arrival[i] <= t and
                      pos_at[i][arrival[i]] == specs[i].goal)
        head.set_text(f"{title}   t = {t:3d}   arrived {arrived}/{n}   "
                      f"collisions {coll}")
        for i in range(n):
            gone = t >= arrival[i] and pos_at[i][arrival[i]] == specs[i].goal and t > arrival[i]
            p = pos_at[i].get(min(t, arrival[i]))
            if gone or p is None:
                dots[i].set_data([], [])
                wins[i].set_data([], [])
                trails[i].set_data([], [])
                continue
            dots[i].set_data([p[0]], [p[1]])
            hist = [pos_at[i][k] for k in range(max(0, t - 6), min(t, arrival[i]) + 1)
                    if k in pos_at[i]]
            trails[i].set_data([c[0] for c in hist], [c[1] for c in hist])
            win = result.windows[t].get(i, []) if t < len(result.windows) else []
            wins[i].set_data([c[0] for c in win], [c[1] for c in win])
        return dots + wins + trails

    anim = FuncAnimation(fig, frame, frames=range(0, t_max + 3), blit=False)
    anim.save(path, writer=PillowWriter(fps=fps), dpi=dpi)
    plt.close(fig)
