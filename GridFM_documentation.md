## Documentation Guidelines

Use this document to record important discussions and findings from work with Claude Code across both GridFM repositories:

- `gridfm-datakit`
- `gridfm-graphkit`

- Write in simple, clear language.
- Do not use em dashes.
- Summarize the key findings, decisions, changes, and open questions.
- Organize information under clear headings.
- Keep related information together.
- Identify the repository for every change, finding, decision, and commit.
- Commit work regularly in small, atomic commits. Each commit should contain one logical change and leave the repository in a usable state.
- After each commit, record the repository name, commit number or short hash, and a one-line summary in the commit log below. Use these identifiers when referring to changes in the rest of the document.
- Periodically review and reorganize the document so it remains a useful overview. Do not simply append new information to the end.

## Background reading (pulled 2026-08-13)

Repository: `gridfm-datakit`

The links listed in `context.md` were pulled and saved under
`docs/references/`. The two arXiv papers were saved as PDF. The blog post, the
Hugging Face and GitHub org pages, and the LF Energy project page were saved as
notes in `docs/references/web_sources_summary.md`, since they are web pages, not
papers. The Joule perspective paper could not be pulled. Cell Press returned
HTTP 403 Forbidden, the article is behind a paywall.

Files saved:
- `docs/references/genco_arxiv_2608.09921.pdf`
- `docs/references/datakit_arxiv_2512.14658.pdf`
- `docs/references/web_sources_summary.md`
- `docs/references/joule_perspective_S2542-4351(24)00470-7.pdf` (added manually
  by the user on 2026-08-13, since automated fetch was blocked)

### GENCO (IBM Research)

GENCO, short for Geometric Neural Corrective Solver, is an open source neural
model that analyzes power grids. It uses a graph transformer with corrective
layers and physics decoders, and scales to grids up to 10,000 buses. One model
handles power flow, optimal power flow, and state estimation, tasks that are
normally solved with separate tools. Claimed speedups are up to 30x over AC
solvers for power flow and up to 85x over interior point solvers for
optimization. It was validated on Hydro-Quebec's real 1,200 bus transmission
network. The GridFM Development Framework that supports it includes open
datasets with 4 million instances across 6 topologies.

### gridfm-datakit paper

Title: "gridfm-datakit-v1: A Python Library for Scalable and Realistic Power
Flow and Optimal Power Flow Data Generation." This is the paper for this
repository. It describes three gaps the library fills in existing data
generation tools: limited scenario diversity, datasets restricted to feasible
operating points, and inflexible generator cost functions. It compares the
library against OPFData, OPF-Learn, PGLearn, and PF-Delta.

### GridFM on Hugging Face and GitHub

The GridFM organization on Hugging Face is affiliated with LF Energy and has
published 31 datasets, mainly OPF data built on IEEE test cases (case14 through
case2000) and PFDelta task data. No public models are listed yet.

The GridFM organization on GitHub hosts two repositories: `gridfm-datakit`
(this repository, data generation) and `gridfm-graphkit` (foundation model
training and inference).

### OpenGridFM and LF Energy

OpenGridFM is the umbrella project under LF Energy, a Linux Foundation project.
Its stated goal is to enable foundation models for power grids with a
significant computation speed advantage over classical tools. `gridfm-datakit`
and `gridfm-graphkit` are its two repositories.

### Joule perspective paper

Title: "Foundation models for the electric power grid." Published in Joule,
December 18, 2024. Authors include Hendrik F. Hamann, Blazhe Gjorgiev, Thomas
Brunschwiler, Alban Puech, and a large group of co-authors from IBM Research,
Hydro-Quebec, NREL, Argonne, ETH Zurich, and other institutions.

The paper argues that foundation models, the kind used for language and
weather, can be developed for the electric power grid. It calls this class of
models grid foundation models, or GridFMs. The authors claim GridFMs could
speed up computation by at least 3 to 4 orders of magnitude compared to
classical methods, and that their generalizability lets stakeholders fine-tune
one model for their own proprietary data cheaply and at scale. The paper
covers the strengths and weaknesses of the approach given a changing grid, and
lays out a practical road map for GridFM-v0, a first grid foundation model for
power flow based on graph neural networks. It closes by discussing downstream
use cases for this and future GridFMs.

This paper is the conceptual basis for the GridFM project as a whole,
including `gridfm-datakit` and `gridfm-graphkit`, and predates GENCO and the
datakit paper.

## Local environment setup (2026-08-13)

Repository: `gridfm-datakit`

Set up the repository to run locally with `uv`.

- Created `.venv` with Python 3.12.11, within the project's required range of
  3.10 to 3.12. Already excluded by `.gitignore`.
- Installed the package with the `test` and `dev` extras.
- Ran `uv lock` and committed `uv.lock`, so `uv sync` reproduces the same
  environment.
- Confirmed the CLI works (`gridfm_datakit --help`) and a subset of the pure
  Python test suite passes (28 tests, `test_topology_perturbation.py` and
  `test_generator_perturbation.py`).
- Installed the Julia side with `gridfm_datakit setup_pm`. Julia itself
  (version 1.12.5) was already present on the machine. This installs
  PowerModels, Ipopt, and Memento, and is required for actual data
  generation, not just for importing the package.

## Experiments (2026-08-13 to 2026-08-14)

Repository: `gridfm-datakit`

All experiments use `case24_ieee_rts` unless stated otherwise, with a fixed
seed of 42 for comparability. Configs live in `scripts/config/smoke_test*.yaml`.
Output data is written under `data_out/`, which is gitignored, so only the
configs are committed. Every run was checked with `gridfm_datakit validate`
and passed all checks.

### Smoke test (baseline)

Config: `smoke_test.yaml`. 50 load scenarios, 5 random topology variants each,
PF mode. 250 scenario-partitions generated in about 30 seconds. No errors.
This confirmed the full pipeline works after setup: load perturbation, topology
perturbation, AC and DC power flow through Julia, and parquet output.

### PF vs OPF

Configs: `smoke_test.yaml` (PF) vs `smoke_test_opf.yaml` (OPF), otherwise
identical settings.

| | PF | OPF |
| --- | --- | --- |
| Scenario-partitions | 250 | 248 (2 dropped, infeasible for OPF) |
| Overloaded branches (> 1.0 loading) | 7 | 0 |
| Binding branch constraints (>= 0.99) | 51 | 56 |
| Mean AC solve time | 0.0007s | 0.0212s (about 30x slower) |
| Mean DC solve time | 0.0003s | 0.0047s (about 16x slower) |

Finding: PF mode is fast and allows operating limit violations by design. OPF
mode is much slower per scenario but guarantees a cost optimal, feasible
dispatch. Some scenario and topology combinations that PF can solve are
infeasible for OPF and get dropped.

### Topology perturbation: random vs n_minus_k

Configs: `smoke_test.yaml` (random) vs `smoke_test_nmk.yaml` (n_minus_k),
otherwise identical settings.

| | random | n_minus_k |
| --- | --- | --- |
| Topologies per load scenario | 5 (sampled) | 38 (exhaustive, all N-1 outages) |
| Total scenario-partitions | 250 | 1900 |
| Overloaded branches (> 1.0) | 7 (2.8%) | 69 (3.6%) |
| Binding constraints (>= 0.99) | 51 | 455 |

Finding: `n_minus_k` ignores the `n_topology_variants` and `elements` settings
and instead enumerates every possible single component outage for the grid.
It is not a sampling strategy with a configurable size, it produces an
exhaustive and much larger dataset per load scenario. The overload rate is
similar between the two modes here, so random sampling looks representative
of the full N-1 space for this small grid, but that may not hold for larger
grids.

### Scale test: Texas2k (2000 buses)

Config: `smoke_test_texas2k.yaml`, a scaled down version of the repository's
existing `Texas2k_case1_2016summerpeak.yaml` (20 scenarios and 2 topology
variants instead of 10000 and 20). PF mode, grid loaded from file.

- 34 of 40 scenario-partitions succeeded. 3 of 20 base scenarios (15%) failed
  with `OPF did not converge: ITERATION_LIMIT`. This happens even in PF mode,
  because the library runs an OPF first to get a base dispatch before
  applying perturbations.
- Mean AC solve time was 0.069s and mean DC solve time was 0.029s, about 100x
  slower than the 24 bus grid.
- Total wall time was about 2 minutes 10 seconds for 20 base scenarios, most
  of it in finding the load scaling upper bound and processing.

Finding: the full `Texas2k_case1_2016summerpeak.yaml` config targets 10000
scenarios and 20 topology variants, which is 200000 scenario-partitions. Based
on this test, that run should be budgeted in hours, not minutes, and a similar
convergence dropout rate should be expected unless `global_range` or
`max_scaling_factor` are tightened.

### Admittance perturbation sigma sweep

Configs: `smoke_test_admittance_low.yaml` (sigma 0.05) vs
`smoke_test_admittance_high.yaml` (sigma 0.8), otherwise identical to
`smoke_test.yaml` (which uses sigma 0.2).

| | sigma 0.05 | sigma 0.8 |
| --- | --- | --- |
| Y-bus G standard deviation | 7.08 | 21.29 |
| Y-bus B standard deviation | 51.29 | 69.07 |
| Overloaded branches (> 1.0) | 7 | 13 |
| Binding constraints (>= 0.99) | 58 | 65 |

Finding: raising `admittance_perturbation.sigma` increases the spread of the
Y-bus admittance values as expected, and this carries through to more branch
overloads and binding constraints in the resulting PF data. The setting
behaves as documented and gives a usable lever for controlling dataset
diversity.

## ML task coverage (2026-08-14)

Repository: `gridfm-datakit`, plus a check against `gridfm-graphkit`

To answer the question of what ML tasks this data actually supports, the
`gridfm-graphkit` sister repo was checked directly for implemented task
types, rather than guessing from the schema alone. It registers three tasks,
all built as a shared "masked node feature reconstruction" pattern
(`ReconstructionTask` base class in `gridfm_graphkit/tasks/`):

- `PowerFlow` — reads `gridfm-datakit` PF-mode output, including the
  operating-limit-violated scenarios PF mode intentionally produces.
- `OptimalPowerFlow` — reads OPF-mode output, always feasible and
  cost-optimal by construction.
- `StateEstimation` — reconstructs full state from a masked/noisy subset of
  measurements, simulated on top of the full ground truth.

`gridfm-graphkit`'s dataset loader
(`gridfm_graphkit/datasets/powergrid_hetero_dataset.py`) reads
`bus_data.parquet`, `gen_data.parquet`, and `branch_data.parquet` directly by
filename, so the schema is a real contract between the two repos, not just
a convenient CSV dump.

Beyond those three implemented tasks, the schema also supports (not yet
built as registered tasks in `gridfm-graphkit`, would need custom code):
contingency/security screening and topology identification (from
`br_status` plus the `n_minus_k` exhaustive outage labels), line
resistance/reactance estimation from flows (using the admittance-perturbed
branches), DC-to-AC correction (both are stored for the same scenario),
solver-runtime/convergence-difficulty prediction (from `runtime_data.parquet`
and Ipopt logs), infeasibility/loadability-boundary prediction (from
`error.log` and the scaling-factor search in `scenarios_*.log`), and
cross-grid or cross-cost-regime generalization studies (just a config sweep).

What the data cannot support at all: dynamics (frequency, rotor angle,
transient/small-signal stability), unit commitment (no ramping or multi
period coupling, every scenario is independent), and locational marginal
prices (PowerModels computes duals, but the output schema in
`gridfm_datakit/utils/column_names.py` has no column for them, so this would
need a code change first).

## Overnight batch dataset generation plan (2026-08-14)

Repository: `gridfm-datakit`

Following the ML task coverage discussion above, the plan is to generate one
dataset per task family, at small, medium, and large grid scale where it
makes sense, and run the whole batch overnight.

Decisions made with the user before building this:

- No hard time budget (12+ hours is fine).
- Run datasets sequentially, one at a time, each using all 32 cores
  (`num_processes: 32`), rather than several jobs competing for cores at
  once.
- Keep the batch tied to this Claude Code session rather than launching a
  detached `nohup` process. This was an explicit choice by the user, made
  knowing that if the session ends, the batch stops with it.
- Add a medium grid tier between the small and large ones for each dataset
  group, not just small/big extremes.

To size the exhaustive `n_minus_k` contingency datasets correctly (the
number of topologies scales with branch count, since `k=1` yields
`branches + 1` topologies per load scenario), bus/branch/generator counts
were measured directly by loading each candidate grid:

| Grid | Buses | Branches | Generators |
| --- | --- | --- | --- |
| case14_ieee | 14 | 20 | 5 |
| case24_ieee_rts | 24 | 38 | 33 |
| case57_ieee | 57 | 80 | 7 |
| case118_ieee | 118 | 186 | 54 |
| case300_ieee | 300 | 411 | 69 |
| case500_goc | 500 | 733 | 224 |
| case2000_goc | 2000 | 3639 | 384 |
| Texas2k (file-based) | 2000 | 3220 | 544 |

The eight dataset groups, each mapped to a task family:

1. **PF baseline** (`case14_ieee` / `case118_ieee` / `case2000_goc`) — for
   the `PowerFlow` task.
2. **OPF baseline** (`case24_ieee_rts` / `case118_ieee` / `case500_goc`) —
   for the `OptimalPowerFlow` task.
3. **Contingency exhaustive** (`case24_ieee_rts` / `case118_ieee` /
   `case2000_goc`, `n_minus_k`, `k=1`) — for contingency screening and
   topology identification.
4. **Line parameter estimation** (`case24_ieee_rts` / `case118_ieee`, fixed
   topology, wide admittance sweep `sigma=1.5`) — for R/X inference from
   flows.
5. **Solver difficulty** (all 7 grids from the sizing table above, Ipopt
   logging enabled, fast solvers disabled so Ipopt actually logs) — for
   runtime/convergence-difficulty prediction.
6. **Loadability boundary** (`case57_ieee` / `case300_ieee` /
   `case2000_goc`, higher per-bus load noise `sigma=0.35`) — for
   infeasibility-boundary labels, read from `error.log`.
7. **Cost-regime sweep** (`case57_ieee`, OPF, `cost_perturbation` with
   sigma in `{0.2, 1.0, 2.5}`) — for generalization across cost
   distributions.
8. **Cross-grid generalization** (all 7 grids from the sizing table,
   identical perturbation config) — for scale/topology transfer studies.

DC-to-AC correction data needs no separate dataset: `include_dc_res: true`
is set on every job above, so paired AC/DC results come for free.

### Files

- `scripts/overnight_batch/generate_configs.py` — builds all 31 dataset
  configs (one YAML per dataset under `scripts/config/overnight/`) plus a
  `manifest.json` describing each dataset's purpose, grid, mode, and
  scenario count. Has been run; the configs and manifest exist under
  `scripts/config/overnight/`.

### Open item

The sequential driver script that runs every config in the manifest one
after another (`run_all.py`) was drafted but the file write was denied by
the user, so it has not been created yet. The config generator itself has
been run and the configs exist, but the batch has not started.

## Overnight batch: execution and results (2026-08-14)

Repository: `gridfm-datakit`

Follow-up to the plan recorded above. The batch ran overnight as a fully
detached process (survives the terminal session ending), with two live
fixes applied while it ran:

- `contingency_large_case2000` had `pf_fast: false` in its generated config.
  On a grid this size, with exhaustive `n_minus_k` multiplying the
  per-scenario solve count by branches-in-service (3634 for `case2000_goc`),
  this turned into a multi-hour job. Confirmed live: 32 workers at 99% CPU,
  zero completed scenarios after 38 minutes. Fixed in both the live config
  and `generate_configs.py`.
- Even after that fix, `case2000_goc` (3639 branches, the clear outlier
  among the grids used) was still too slow at the planned sizes for a
  single workstation. Deferred four datasets to be run on HPC instead:
  `contingency_large_case2000`, `solver_difficulty_case2000_goc`,
  `loadability_case2000_goc`, `crossgrid_case2000_goc`. Their configs are
  untouched and ready to run anywhere `gridfm-datakit` and Julia are set
  up, no extra packaging needed. `pf_large_case2000`, which had already
  finished (about 21 minutes), was left as done.
- The batch driver (`run_all.py`) originally launched each dataset
  subprocess in the same process group as itself. Killing a stuck job's
  process group took down the whole driver by accident. Fixed by launching
  each dataset subprocess with `start_new_session=True`, so a stuck job can
  be killed on its own from then on.

Final result: 27 of 31 datasets completed, 0 failed, 4 deferred to HPC.
Every completed dataset was checked with `gridfm_datakit validate`
(`scripts/overnight_batch/validate_all.py`): 27 out of 27 passed all 21
validation checks.

## gridfm-graphkit: setup, capability analysis, and experiments (2026-08-14)

Repository: `gridfm-graphkit`

### Setup

Set up with `uv`, same as `gridfm-datakit`, but with a real GPU available
on this machine (NVIDIA RTX 4500 Ada, 24GB, driver CUDA 12.8). Routed
`torch`/`torchvision`/`torchaudio` through an explicit `pytorch-cu128`
index in `pyproject.toml` so `uv sync` resolves CUDA wheels instead of
CPU-only ones. Confirmed with `torch.cuda.is_available()` and a GPU matmul.

Found and fixed a real packaging bug along the way: `torch_scatter` is
imported directly in `training/loss.py` but was never declared as a
dependency. A clean install fails with `ModuleNotFoundError`. Added it,
pinned to the exact PyG wheel matching `torch==2.10.0+cu128` (PyG has no
real package index for it, only per-torch-version wheel pages).

### Capability analysis

Wrote `docs/CAPABILITIES.md` (1484 lines, 15 sections) by reading the
source directly. Confirmed findings, verified against source directly, not
just accepted from the analysis pass:

- `MaskedBusMSE` loss has a comparison bug.
- `DATASET_WRAPPER_REGISTRY` is defined but never populated (the
  `--dataset_wrapper` CLI flag references a plugin mechanism with nothing
  registered).
- `StateEstimationTask.predict_step` is a no-op stub.
- `NUM_PROCESSES = 64` is hardcoded into the baseline runtime normalization
  in `pf_ac_dc_baseline.py`.
- `examples/notebooks/Tutorial_reconstruction_visualization.ipynb` imports
  `LitGridDataModule` and `FeatureReconstructionTask`, neither of which
  exists anywhere in the current codebase. Leftovers from a pre-`HeteroData`
  version of the package. The notebook fails on its first import cell as
  shipped.

### Experiments

All experiments trained on real `gridfm-datakit` output from the overnight
batch above, not synthetic or toy data.

Smoke test first: `PowerFlow` task, `GNS_heterogeneous` model, 5 epochs, on
`pf_small_case14` (3000 scenarios, 14999 graphs after topology
perturbation). Data loading, GPU training, and test evaluation all ran
cleanly in under a minute. Hit one real bug in the process: the pinned
`mlflow>=3.1.0` has deprecated the filesystem tracking backend that
`gridfm_graphkit train` uses by default, so a stock invocation crashes
immediately unless `MLFLOW_ALLOW_FILE_STORE=true` is set or `--log_dir`
points at a database URI.

Three comparisons, all using real data from last night's batch:

**Model architecture, `GNS_heterogeneous` vs `GRIT`, same task and data
(`case14_ieee`, `PowerFlow`).** The two use different loss compositions,
so their test metrics are not directly comparable numbers, but wall clock
is: GRIT took about 9.1 seconds per epoch against GNS's about 1 second,
roughly 8.5x slower on the same 14 bus grid. Expected given GRIT is a much
heavier model (496 hidden dim, attention, 7 layers versus GNS's 48 hidden
dim, 12 layers).

**Task, `PowerFlow` vs `OptimalPowerFlow` vs `StateEstimation`, all
`GNS_heterogeneous`, matched epoch budget.** PowerFlow and
OptimalPowerFlow both produced a final `--report-performance` test metric.
StateEstimation's test loop ran cleanly (4 of 4 batches) but never printed
a final performance metric, unlike the other two tasks. Worth checking
before relying on `--report-performance` for state estimation runs.

**Grid size scaling, `PowerFlow` + `GNS_heterogeneous`, identical config
across `crossgrid_case14_ieee` through `crossgrid_case500_goc` (14 to 500
buses), 15 epochs each.** Per-epoch training time scaled sub-linearly with
grid size: about 1 second at 14 buses, about 7.6 seconds at 500 buses,
roughly 7x time for about 36x more buses. Consistent with efficient batched
GPU training. Raw test residuals did not trend cleanly with grid size,
expected since these are unnormalized residuals after only 15 epochs, not
converged quality.

## GridSFM: setup, capability analysis, and experiments (2026-08-14)

Repository: `GridSFM` (Microsoft, not one of the two GridFM repositories
named in this document's guidelines, but closely related work done in the
same session, so recorded here too)

### Setup

`model/` (the `gridsfm` Python package, a pretrained AC-OPF inference
surrogate) set up with `uv`, CUDA 12.8 torch build, same pattern as
`gridfm-graphkit`. `power_grid/` is a pure Julia pipeline plus a small
Python viewer, no `uv` setup needed there. Full test suite passes: 20
passed, 18 skipped.

### Capability analysis

Wrote `docs/CAPABILITIES.md` (978 lines, 15 sections). Corrected two
inaccuracies found in an earlier draft (from a first analysis pass that
died mid-write when the account hit its usage limit, leaving a partial
file behind that a retry pass then verified and fixed rather than
rewriting from scratch):

- The Makefile's `solve`/`local-solve` targets do chain `patch_model.jl`
  before solving. An earlier draft claimed they did not and called this a
  footgun. Confirmed false by reading the current `Makefile` directly.
- The model test suite has exactly 38 tests, not the roughly 60 an earlier
  draft estimated. Confirmed with `pytest --collect-only`.

### Experiments

GridSFM is an inference package built around two released checkpoints
(`gridsfm_open_v1.1.pt` recommended, `v1.0` deprecated), not a training
framework, so the experiments here are inference benchmarks, not training
comparisons.

**Sample benchmark** (`examples/infer_samples.py`, unmodified, as shipped):
ran the recommended checkpoint on all 53 shipped `.pyg.json` samples (14 to
3889 buses), each with a ground truth AC-OPF solution attached. Result: 53
of 53 correctly classified feasible, cost prediction mean error 0.61
percent (median 0.40 percent), voltage MAE 0.003 per unit, angle MAE about
1.2 degrees. Total time for all 53 mixed size grids: 4.0 seconds
preparation plus 1.6 seconds forward pass on GPU. One real outlier:
`case3022_goc` had angle MAE of 12.2 degrees and Pg MAE of 0.13 per unit,
far outside the rest of the pack. Not a size effect, since the larger
`case3375wp_k` did fine. Likely a genuinely hard instance, `goc` cases are
known to be tightly constrained PGLib benchmarks. Caveat on the whole
benchmark: these are the unperturbed base cases the model's own training
perturbations were built from, so this measures in family generalization,
not truly novel data.

**Cache and latency scaling** (small benchmarking script written using
only existing `gridsfm` API calls, no new data or format conversion code,
per explicit instruction not to build new format-bridging tooling for this
session): two findings.

- Per-graph inference latency scales sub-linearly with grid size: about
  2.2x latency for about 7.8x more buses (500 to 3889 buses, 68ms to 152ms).
- Cache warm-up shows a real cold versus warm effect (554ms first call
  versus 106ms mean afterward on a repeated topology, about 5.2x speedup),
  but individual warm call latencies were noisy (51 to 319ms), so the
  caching contribution could not be cleanly isolated from GPU or scheduling
  noise with this simple a benchmark. Real effect, uncertain magnitude.

An idea for a cross-repo experiment was raised and explicitly declined for
this session: converting `gridfm-datakit` OPF ground truth (solved by an
independent PowerModels and Ipopt pipeline) into GridSFM's `.pyg.json`
schema, to test the pretrained model's generalization to data from a
completely different generation pipeline. Two generator fields
(`mbase`, `Vg`) are not present in `gridfm-datakit`'s output and would need
approximated proxies. Not attempted, left as a possible follow-up.

## Commit Log

Record completed work in this format:

| Repository | Commit | Summary |
| --- | --- | --- |
| `<repository>` | `<short hash>` | Brief description of the logical change |
| `gridfm-datakit` | `c764512` | Add background reading references and documentation summary |
| `gridfm-datakit` | `3f746a9` | Add Joule perspective paper and summary |
| `gridfm-datakit` | `3c5ebe5` | Add uv.lock for reproducible installs |
| `gridfm-datakit` | `91e01cb` | Add smoke-test config for quick pipeline verification |
| `gridfm-datakit` | `5b154ae` | Add OPF smoke-test config for PF vs OPF comparison |
| `gridfm-datakit` | `9968db5` | Add n_minus_k topology config for comparison against random sampling |
| `gridfm-datakit` | `54caa98` | Add Texas2k scale-test config |
| `gridfm-datakit` | `bcfca08` | Add admittance-perturbation sigma sweep configs |
| `gridfm-datakit` | `65bf770` | Add full capability reference (docs/CAPABILITIES.md) |
| `gridfm-datakit` | `b10ed07` | Document the pfdelta/opf_data converters and scripts/ tooling |
| `gridfm-datakit` | `788af36` | Document ML task coverage findings and the overnight batch dataset plan |
| `gridfm-datakit` | `7ed2b64` | Generate the 31 overnight-batch dataset configs |
| `gridfm-datakit` | `9d5eb97` | Add sequential driver for the overnight batch dataset run |
| `gridfm-datakit` | `68a864d` | Defer case2000_goc datasets to HPC, fix driver process isolation |
| `gridfm-datakit` | `3c66d51` | Add validate_all.py, confirm all 27 overnight batch datasets pass |
| `gridfm-graphkit` | `8b51422` | Add uv support, pin CUDA torch stack, fix missing torch_scatter dependency |
| `gridfm-graphkit` | `d1e6d5f` | Add full capability reference (docs/CAPABILITIES.md) |
| `gridfm-graphkit` | `946770f` | Add smoke-test config, verify training pipeline end-to-end |
| `gridfm-graphkit` | `8cf8bdc` | Add experiment configs: model/task comparison and grid-size scaling |
| `GridSFM` | `acbe02a` | Set up uv for model/, pinned to CUDA 12.8 torch build |
| `GridSFM` | `c1d2cde` | Add full capability reference (docs/CAPABILITIES.md) |
| `GridSFM` | `58adfe1` | Add small benchmarking script: cache warm-up and latency-vs-size scaling |