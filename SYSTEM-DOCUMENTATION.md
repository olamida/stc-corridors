# SYSTEM-DOCUMENTATION — stc-corridors

Deep technical / developer documentation. For running instructions see
`USER-GUIDE.md`; for the work ledger see `PENDING-TASKS.md`.

## 1. Purpose and scope

Pure-Python tick simulator for decentralized 4D corridor negotiation between ground and aerial agents.

Research question: **How does corridor lookahead H trade safety, delay and bandwidth when the network drops packets?**

This is a simulation study. No hardware measurements, external datasets or
proprietary data are involved. The repository is intentionally small enough to
be read end-to-end by a reviewer in one sitting.

## 2. Architecture

| Component | Responsibility |
|---|---|
| `src/stc/world.py` | 3D grid, blocked cells, ground/air kinematics, BFS distance maps. |
| `src/stc/planner.py` | Space-time A* plus vertex/swap constraint table. |
| `src/stc/protocol.py` | Reservation message, local table, newest-wins update, first-conflict test. |
| `src/stc/agent.py` | Per-agent plan/replan logic with priority-aware fallbacks. |
| `src/stc/sim.py` | Three-mode tick executor and ground-truth collision counting. |
| `src/stc/scenarios.py` | Seeded crossing, corridor, open_grid and mixed_city scenario builders. |
| `src/stc/viz.py` | Matplotlib renderer used by the demo animation. |

Dependencies flow one way: configuration/scenario → model/algorithm →
experiment runner → results → figures/animation. The simulator does not read
its own results; results are an output only.

## 3. Data flow

1. A seeded scenario, task set, signal or topology is constructed.
2. The core model advances in discrete steps (ticks or control steps).
3. Metrics are accumulated independently of the decision logic where possible
   (for example, a ground-truth collision checker rather than the agents' beliefs).
4. `experiments/` writes machine-readable results under `results/`.
5. `make_figures.py` and `make_animation.py` read those results or re-run the
   seeded simulator to produce visual artefacts.

## 4. Algorithms / numerical methods

See `README.md` for the high-level description and, where present,
`docs/DESIGN.md` or `DEVELOPMENT_GUIDE.md` for the full derivation. The
implementation is the authoritative reference: start at the module table in
section 2 and follow the entry point used by `pytest -q`.

Reproducibility rules:
- Every stochastic component is driven by an explicit seed.
- Experiment parameters are recorded in the result rows.
- A change to a result number requires regenerating the CSV/JSON, not editing prose.

## 5. Results and evidence

- Lossless, all-arrive-and-collision-free runs: crossing 100% (reactive 0%, central 90%), corridor 2+2 100%, corridor 3+3 83%, open grid 100%, mixed city 100% — `results/methods.csv`.
- At 30% packet loss and H=12, collision-free runs are 90% (open grid) / 100% (mixed city) / 90% (crossing) — `results/loss_sweep.csv`.
- Going from H=2 to H=8 changes 30%-loss results from 37/70/33 to 90/100/83; returns diminish past H≈8 — `results/loss_sweep.csv`.
- Announce-then-act was equal or better in 11 of 12 matched ablations, but every gap is 1–2 runs out of 30 — `results/ablation.csv`.

## 6. Animation pipeline

`python experiments/make_demo.py 15` renders `figures/demo_mixed_city.gif`. It uses the project's own simulator
(or an explicitly documented pure-Python reference of the same controller) and
Matplotlib's Pillow writer. Frames are subsampled to keep the GIF small; the
underlying trajectory is not resampled or smoothed. 16 agents (8 drones + 8 ground vehicles) negotiating a street grid at 30% packet loss; faint segments are broadcast corridors.

## 7. Build, test and CI

```bash
pip install -r requirements.txt
pytest -q
python experiments/run_benchmarks.py && python experiments/make_figures.py
python experiments/make_demo.py 15
```

CI (`.github/workflows/ci.yml`) runs on push and pull request. Jobs install the
documented dependencies, set `PYTHONPATH=src` where required, and run the test
suite. Repositories that call C code install a system compiler in CI; footprint
measurement with cross-compilers is deliberately optional.

## 8. Extension points

- Add a new scenario/policy by extending the corresponding factory or registry
  and a seeded test, then re-run the full experiment suite.
- Add a new metric by writing it into the result row and updating
  `experiments/summarize.py` and the README table together.
- Add a new animation by recording the relevant simulator state (prefer an
  optional `record` flag over duplicating the stepping logic) and saving via
  `FuncAnimation`/`PillowWriter` in `experiments/`.

## 9. Known limitations

- Discrete world with perfect localisation; no dynamics, sensor noise or continuous geometry.
- Agents disappear at their goal; parking and queuing are not modelled.
- Fixed priorities (agent index); low-priority agents can starve.
- No deadlock resolution in the hard single-lane corridor.
- Under packet loss safety degrades gracefully; it is not a formal guarantee.
- Independent per-link loss; real radio loss is bursty and range-dependent.

## 10. Relation to the rest of the portfolio

Formal companion: `stc-formal`. Application study: `pipeline-patrol-swarm`. Longer plan: `docs/PROJECT_LADDER.md`.

## 11. Release metadata

`CITATION.cff` carries title, author (Yusuf Ndanusa Yahaya), version 0.1.0,
release date, repository URL and MIT license. No DOI or ORCID is claimed.
