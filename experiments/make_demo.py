"""Render the demo GIF: mixed ground/air traffic with 30% packet loss."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from stc import SCENARIOS, SimConfig, run  # noqa: E402
from stc.viz import render_gif  # noqa: E402

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 3
out = os.path.join(os.path.dirname(__file__), "..", "figures", "demo_mixed_city.gif")
world, specs = SCENARIOS["mixed_city"](n_ground=8, n_air=8, seed=SEED)
cfg = SimConfig(mode="stc", horizon=12, loss=0.3, seed=SEED, record=True)
res = run(world, specs, cfg)
print(f"seed={SEED} success={res.success} collisions={res.collision_events} "
      f"makespan={res.makespan} delay={res.mean_delay:.2f} replans={res.replans} "
      f"lost={res.messages_lost}/{res.messages_sent}")
render_gif(world, specs, res, out, fps=5, title="STC, 30% packet loss")
print("wrote", os.path.relpath(out))
