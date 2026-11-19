# USER-GUIDE — stc-corridors

End-user manual. You do not need to edit code to follow this guide.

## 1. What you can do with it

Pure-Python tick simulator for decentralized 4D corridor negotiation between ground and aerial agents.

The research question is: *How does corridor lookahead H trade safety, delay and bandwidth when the network drops packets?*

## 2. Install

```bash
git clone https://github.com/olamida/stc-corridors.git
cd stc-corridors
pip install -r requirements.txt
```

Python 3.10+ is assumed. On Windows use `.venv\Scripts\activate` instead of
`source .venv/bin/activate` if you create a virtual environment.

## 3. Watch the animation

Open `figures/demo_mixed_city.gif` directly on GitHub or in any image viewer; GitHub plays
GIFs inline. The animation shows: 16 agents (8 drones + 8 ground vehicles) negotiating a street grid at 30% packet loss; faint segments are broadcast corridors.

To regenerate it from source:

```bash
python experiments/make_demo.py 15
```

## 4. Verify the installation

```bash
pytest -q
```

A passing run prints a test summary with no failures. If a C compiler is
mentioned as missing, install a system C compiler (gcc on Linux, Xcode command
line tools on macOS, MinGW/MSVC on Windows) and rerun.

## 5. Run the full experiments

```bash
python experiments/run_benchmarks.py && python experiments/make_figures.py
```

Outputs appear in `results/` (CSV/JSON/Markdown tables) and `figures/`
(PNG/GIF). Re-running with the shipped seeds should reproduce the shipped
numbers; small differences can occur with different library versions.

## 6. How to read the outputs

- Lossless, all-arrive-and-collision-free runs: crossing 100% (reactive 0%, central 90%), corridor 2+2 100%, corridor 3+3 83%, open grid 100%, mixed city 100% — `results/methods.csv`.
- At 30% packet loss and H=12, collision-free runs are 90% (open grid) / 100% (mixed city) / 90% (crossing) — `results/loss_sweep.csv`.
- Going from H=2 to H=8 changes 30%-loss results from 37/70/33 to 90/100/83; returns diminish past H≈8 — `results/loss_sweep.csv`.
- Announce-then-act was equal or better in 11 of 12 matched ablations, but every gap is 1–2 runs out of 30 — `results/ablation.csv`.

## 7. Known limitations (please read)

- Discrete world with perfect localisation; no dynamics, sensor noise or continuous geometry.
- Agents disappear at their goal; parking and queuing are not modelled.
- Fixed priorities (agent index); low-priority agents can starve.
- No deadlock resolution in the hard single-lane corridor.
- Under packet loss safety degrades gracefully; it is not a formal guarantee.
- Independent per-link loss; real radio loss is bursty and range-dependent.

## 8. Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError` | Running from the wrong directory or missing `PYTHONPATH=src` | Run from the repository root and use the exact command in section 4. |
| Build fails with "gcc not found" | No system C compiler | Install gcc/Xcode CLT/MinGW; the pure-Python reference is only for the animation. |
| Animation script cannot find sibling repo | `stc-corridors` not beside `stc-formal` | Clone both repositories side by side, or install `stc` into the environment. |
| Numbers differ from README | Different seeds or library versions | Use the command in section 5 and compare against `results/` in the repo. |

## 9. Getting help

Open an issue with the exact command, your OS/Python version and the last 20
lines of output. Please do not attach private or employer data.
