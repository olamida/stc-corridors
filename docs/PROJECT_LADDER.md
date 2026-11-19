# Project ladder: how the portfolio grows

Everything below runs **in simulation on a laptop**. Each rung adds one new skill, produces one public artefact, and answers one question a supervisor might ask. Work on one rung at a time; ship it (README + results + CI) before starting the next.

**Rules for every repo**

1. README order: question -> method -> results table/figure -> **limitations** -> reproduce in one command.
2. Seeded, scripted experiments; numbers in the README must come from files in `results/`.
3. Tests + CI (GitHub Actions). MIT licence.
4. Never use confidential or real operational data. Use synthetic or public data only.
5. Tag a release when a rung is done (`v0.1`, `v0.2`...) so progress is visible on the profile.

---

## Rung 0 · `stc-corridors` (done, v0.1)

Decentralized corridor negotiation under packet loss. **Shows:** you can design, implement, test and honestly evaluate a multi-agent protocol.

## Rung 1 · Foundations (weeks 1-6)

| # | Repo | Build | New skill | Evidence |
|---|---|---|---|---|
| 1 | `embedded-autonomy-sim` | Differential-drive robot with line following + obstacle avoidance. Control loop written in **portable C** (fixed-point Q15), called from a Python simulator via `ctypes`. Compare fixed-point vs floating-point tracking error; report code size and a per-iteration operation count. | Embedded C in simulation, numerics, honest resource accounting | Table: tracking error vs word length; "this loop would fit an 8-bit MCU budget" claim backed by operation counts |
| 2 | `lite-perception` | Pedestrian / obstacle detection on **synthetic rendered frames** and a public dataset (classical OpenCV first, small quantised model second); intent estimate from tracked motion. | Perception pipelines, profiling | Accuracy vs latency vs memory table (builds on your 2019 OpenCV work) |

## Rung 2 · Core research thread (weeks 6-20)

| # | Repo | Build | New skill | Evidence |
|---|---|---|---|---|
| 3 | `stc-formal` | Add a **safety filter** (control barrier function or STL-based monitor) on top of `stc-corridors`; property-based tests (Hypothesis) and exhaustive search on tiny grids to find counter-examples; derive and test a loss-probability bound for missed conflicts. | Formal methods, runtime verification, property testing | Counter-example list + a bound that the simulation either confirms or refutes |
| 4 | `stc-human-aware` | Add pedestrians (constant-velocity and social-force models); inflate corridors by predicted intent; measure near-misses vs delay. | Prediction under uncertainty | Safety/efficiency Pareto plot |
| 5 | `stc-comms` | Realistic network model: bursty loss (Gilbert-Elliott), range limits, latency, bandwidth caps; compare broadcast vs acknowledged reservations. | Network modelling, protocol trade-offs | Bandwidth vs safety curves; recommended H per network regime |
| 6 | `stc-deadlock` | Fix the known failure (3+3 corridor squeeze): deadlock detection, dynamic priority, negotiated back-off. | Distributed algorithms | Success rate on hard scenarios before/after |

## Rung 3 · Application studies (weeks 20-32) , choose per target

| # | Repo | Fits | Build |
|---|---|---|---|
| 7 | `pipeline-patrol-swarm` | PTDF / oil & gas; Gulf and European robotics groups | UAV + UGV fleet patrolling a pipeline graph with random "tamper events" and 30% agent loss; metrics: time-to-detect, coverage, graceful degradation. |
| 8 | `grid-edge-theft-detection` | Energy-systems labs; Hong Kong smart-city themes | Synthetic smart-meter data with injected non-technical losses; compare a decision tree and a tiny quantised network; report accuracy vs model size (KB) vs inference cost. |
| 9 | `training-impact-evaluation` (optional) | Professional-doctorate / evaluation tracks | Quasi-experimental analysis (difference-in-differences) on **synthetic or public** workforce-training data; reproducible notebook. |

## Rung 4 · Consolidation (weeks 32-48)

| # | Artefact | Notes |
|---|---|---|
| 10 | **Technical report** (6-8 pages): "Lookahead-limited corridor negotiation under packet loss" | Built from rungs 0, 3, 5, 6. Post on TechRxiv or Zenodo (arXiv needs an endorser for first-time authors); then target a robotics workshop. Ask a co-author or mentor to review first. |
| 11 | `stc-ros2` | Port the protocol to ROS 2 nodes; simulate in Gazebo. Still no hardware needed. Shows middleware skills. |
| 12 | Open-source contribution | One accepted PR (docs, tests or a small fix) to a project in your area, e.g. a ROS 2 / navigation / flight-controller repo. |

---

## Skills matrix (what a supervisor should see growing)

| Capability | R0 | R1 | R2 | R3 | R4 |
|---|:-:|:-:|:-:|:-:|:-:|
| Algorithm design & testing | ● | ● | ● | ● | ● |
| Embedded / resource constraints | | ● | | ● | ● |
| Perception | | ● | ● | | |
| Formal safety / verification | | | ● | | ● |
| Networking / comms realism | ○ | | ● | ● | |
| Domain application (energy, pipelines) | | | | ● | ● |
| Writing & scientific method | ● | ● | ● | ● | ● |
| Middleware (ROS 2) | | | | | ● |

○ = basic, ● = demonstrated.

## Weekly rhythm (sustainable alongside a full-time job)

* 3 focused evenings: code + tests.
* 1 evening: write results into the README, record a short GIF.
* 1 weekend block per month: read two papers on the rung's topic and note what you would do differently.
* Every two weeks: send one short progress note to your mentor or a professor who has replied.
