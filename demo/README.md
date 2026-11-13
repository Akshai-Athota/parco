# HCVRP delivery simulator

An interactive demo: place delivery orders on a map, then watch each trained
checkpoint plan the fleet and compare them side by side.

![what it does](#) <!-- place orders → plan → animate → compare -->

It answers the question the tables cannot: *what does a 3% better objective
actually look like?* You see the routes, you watch the vans move, and you watch
which one finishes last — because the last van to finish **is** the objective
(`max_m distance_m / speed_m`).

## What you can do

- **Place orders** by clicking the map; click an order again to delete it.
  Circle size is the order's demand. Drag the depot anywhere.
- **Generate scenarios** — uniform, three neighbourhoods, two districts, ring
  road — with a seed, so the same scenario is reproducible in the talk.
- **Edit the fleet**: per-vehicle capacity and speed, add or remove vans.
- **Pick planners**: parallel PARCO, k = 1 / 2 / 4 / 7, the corrected tanh
  model, and a classical nearest-neighbour reference.
- **Compare**: longest route (the objective), gap vs parallel PARCO, total
  distance, decoder passes, and solve time.
- **Animate**: scrub or play the clock and watch deliveries land.
- **Per-vehicle breakdown**: who is the bottleneck, how many trips, how many
  orders each van carried.

## Running it

Everything is standard library — no Flask, no extra install.

```bash
python demo/server.py
```

Then open <http://127.0.0.1:8000>.

**On the cluster** (the checkpoints live there), run it on the login node and
forward the port from your laptop:

```bash
ssh -L 8000:localhost:8000 athota@master
```

CPU is plenty — one instance of 40 orders solves in well under a second per
method, so no GPU and no SLURM job is needed.

### Check it before you demo

```bash
python demo/selftest.py
```

For every checkpoint it finds, this solves one instance and verifies that

1. the policy runs and returns actions,
2. the routes we draw reproduce **the environment's own reward** — if these ever
   disagree, the picture on screen does not match the number in the table, and
   the UI says so rather than quietly lying,
3. the solution is feasible: every order served exactly once, nobody over
   capacity.

Non-zero exit means do not demo until it is fixed.

### Without the models

```bash
python demo/server.py --mock
```

Serves only the nearest-neighbour baseline. The UI, the map, the animation and
the comparison table are all identical, so you can build and rehearse the demo
on a laptop with no `rl4co` installed. The header shows a warning badge
whenever the real models are not loaded, so this can never be mistaken for
model output. If `rl4co` or the checkpoints are missing, the server falls back
to this automatically and prints the reason.

## Options

| Flag | Default | Meaning |
|---|---|---|
| `--port` | `8000` | port to serve on |
| `--host` | `127.0.0.1` | bind address; leave as-is unless you know why |
| `--runs-root` | `logs/train/runs/hcvrp_n100_m7` | where the run folders live; resolved relative to the repo root too |
| `--device` | `cpu` | `cuda` if you have a GPU, but CPU is fine |
| `--mock` | off | skip the models entirely |

## A caveat worth saying out loud

The checkpoints were trained on **N ~ U(60, 100) customers and M ~ U(3, 7)
vehicles**, demands 1–9, capacities 20–41, speeds 0.5–1.0. You can set anything
you like, and the models will still produce a plan — but outside those ranges
you are measuring generalisation, not the in-distribution quality the report
tables describe. The UI warns you when a scenario leaves the trained range
rather than presenting the number as comparable.

A single hand-placed instance is also one sample. Our reported gaps are means
over 12 test sets of 1,280 instances each; on any one scenario the ordering of
the methods can easily differ from the average. The demo is for intuition about
*how* the methods behave, not evidence about which is better.

## Files

| File | Role |
|---|---|
| `server.py` | stdlib HTTP server: static files + `/api/methods`, `/api/generate`, `/api/solve` |
| `backends.py` | `TorchBackend` (real checkpoints), `HeuristicBackend` (no deps), and the composite with fallback |
| `routes.py` | actions → routes, timelines and fleet stats; pure arithmetic, no torch |
| `scenarios.py` | scenario generators, training distribution, out-of-range checks |
| `selftest.py` | pre-demo verification |
| `static/` | the single-page UI |

`routes.py` carries the node-indexing contract: `locs` holds the depot repeated
once per agent and then the customers, so action `a < M` is agent `a`'s depot
and `a >= M` is customer `a - M`. An agent "stays" by reselecting its current
node, which the environment treats as a no-op, so consecutive duplicates
collapse; the environment closes each tour at the depot when it scores, so we do
the same.
