# APP-GUIDE — stc-corridors

**Question:** How does corridor lookahead H trade safety, delay and bandwidth when the network drops packets?

**One-line summary:** Pure-Python tick simulator for decentralized 4D corridor negotiation between ground and aerial agents.

This guide records what the application/project has already done and what is still
to be done. It is the session-to-session entry point: read this first, then
`USER-GUIDE.md` to run it, `SYSTEM-DOCUMENTATION.md` to change it, and
`PENDING-TASKS.md` for the live work ledger.

## Work already executed

- Built a discrete 3D world (x, y, z, t) with ground vehicles and drones that may fly over buildings but must descend through street canyons.
- Implemented cooperative space-time A* with vertex and head-on-swap constraints; waiting is a legal action used for yielding.
- Implemented the reservation protocol (broadcast of the next H cells, newest-corridor table, priority-based yielding, announce-then-act) and an adjacent-cell safety stop.
- Implemented three comparable modes in one executor: `stc`, `reactive` baseline and `central` prioritized oracle, with an independent ground-truth collision checker.
- Ran seeded benchmark suites (methods, loss sweep, ablation), 30 seeds per cell; results are in `results/*.csv` and `results/summary.md`.
- Wrote 14 tests (planner, protocol, end-to-end, determinism, loss injection) and a GitHub Actions workflow.
- Produced the hero animation `figures/demo_mixed_city.gif` with `experiments/make_demo.py`.

## Work to be executed (next)

- Resolve the 3+3 single-lane deadlock (about 17% of lossless seeds still fail).
- Add a formal safety filter (STL monitor / control barrier function) and a quantified loss bound; see `stc-formal`.
- Add human-aware planning with predicted intent (`stc-human-aware`).
- Replace independent per-link loss with bursty, range-dependent communication (`stc-comms`).
- Test scaling beyond 16 agents and add continuous dynamics / MPC corridor tracking.

## High-level flow

1. Configure a seeded scenario / task set / signal.
2. Run the simulator or experiment script in this repository.
3. Metrics are written to `results/`; figures to `figures/`.
4. The animation in `figures/demo_mixed_city.gif` is rendered from the same simulator state.

## Commands at a glance

| Purpose | Command |
|---|---|
| Install | `pip install -r requirements.txt` |
| Verify | `pytest -q` |
| Experiments | `python experiments/run_benchmarks.py && python experiments/make_figures.py` |
| Animation | `python experiments/make_demo.py 15` |

## Where this connects

Formal companion: `stc-formal`. Application study: `pipeline-patrol-swarm`. Longer plan: `docs/PROJECT_LADDER.md`.

## Honesty notes

All numbers quoted in this repository come from files under `results/`.
Simulation-only results are not hardware measurements, and the documented
limitations in `README.md` are part of the deliverable.
