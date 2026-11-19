"""Run all benchmarks and write CSVs to ./results.

    python experiments/run_benchmarks.py            # full run (~few minutes)
    python experiments/run_benchmarks.py --quick    # smoke run (seconds)

Everything is seeded: same command, same numbers.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from stc import SCENARIOS, SimConfig, run  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results")

SCEN_KW = {
    "crossing": {},
    "corridor": {"n_each": 2},
    "corridor_hard": {"n_each": 3},
    "open_grid": {},
    "mixed_city": {},
}


def _one(job):
    exp, scen, mode, horizon, loss, announce, sensing, seed = job
    base = "corridor" if scen.startswith("corridor") else scen
    world, specs = SCENARIOS[base](seed=seed, **SCEN_KW[scen])
    cfg = SimConfig(mode=mode, horizon=horizon, loss=loss, announce_first=announce,
                    sensing=sensing, seed=seed)
    r = run(world, specs, cfg)
    return dict(
        experiment=exp, scenario=scen, mode=mode, horizon=horizon, loss=loss,
        announce_first=int(announce), sensing=int(sensing), seed=seed,
        n_agents=r.n_agents, arrived=r.arrived, success=int(r.success),
        collision_free=int(r.collision_events == 0),
        collision_events=r.collision_events, collision_pairs=r.collision_pairs,
        makespan=r.makespan if r.makespan is not None else "",
        mean_delay=round(r.mean_delay, 4) if r.mean_delay is not None else "",
        messages_sent=r.messages_sent, messages_lost=r.messages_lost,
        replans=r.replans, expansions=r.expansions,
        plan_failures=r.plan_failures, safety_stops=r.safety_stops)


def write(name, rows):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {os.path.relpath(path)} ({len(rows)} rows)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--procs", type=int, default=2)
    args = ap.parse_args()
    global OUT
    if args.quick:                       # never overwrite the full results
        OUT = os.path.join(OUT, "quick")
    seeds = range(6) if args.quick else range(30)
    losses = [0.0, 0.3, 0.6] if args.quick else [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    horizons = [2, 12] if args.quick else [2, 4, 8, 12]

    jobs_methods = [("methods", s, m, 12, 0.0, True, True, sd)
                    for s in SCEN_KW for m in ("reactive", "central", "stc") for sd in seeds]
    jobs_sweep = [("loss_sweep", s, "stc", h, p, True, True, sd)
                  for s in ("crossing", "open_grid", "mixed_city")
                  for h in horizons for p in losses for sd in seeds]
    jobs_ablate = [("ablation", s, "stc", 12, p, a, se, sd)
                   for s in ("crossing", "open_grid", "mixed_city")
                   for p in (0.0, 0.3) for a, se in itertools.product((True, False), (True, False))
                   for sd in seeds]

    t0 = time.time()
    with Pool(args.procs) as pool:
        for name, jobs in (("methods.csv", jobs_methods), ("loss_sweep.csv", jobs_sweep),
                           ("ablation.csv", jobs_ablate)):
            print(f"running {name}: {len(jobs)} runs")
            rows = pool.map(_one, jobs, chunksize=8)
            write(name, rows)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
