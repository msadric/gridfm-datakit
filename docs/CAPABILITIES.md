# gridfm-datakit — Full Capability Reference

This is a from-source reference of everything `gridfm-datakit` can do: every
CLI command, every config option, every perturbation type, every output
column, and every code path, including options that are not documented in
the top-level `README.md`. It was written by reading the package source
directly (`gridfm_datakit/`), not by summarizing the existing manual pages,
so it should be treated as authoritative if the two ever disagree.

For narrower deep-dives on individual components, see `docs/manual/*.md` and
`docs/components/*.md`. For local experiment results (PF vs OPF, topology
`random` vs `n_minus_k`, scale test, sigma sweeps) see `GridFM_documentation.md`
in the repository root.

## 1. What the library does

`gridfm-datakit` turns a MATPOWER-format power grid case into a large,
diverse dataset of power-flow (PF) and optimal-power-flow (OPF) scenarios,
suitable for training ML/foundation models. Starting from one base grid, it
applies four independent, composable kinds of perturbation:

1. **Load** — scale and add noise to bus demand over many scenarios.
2. **Topology** — take lines/transformers/generators out of service.
3. **Generator cost** — permute or rescale generator cost curves.
4. **Admittance** — perturb line resistance/reactance.

then solves AC (and optionally DC) power flow/OPF for every resulting
combination via Julia's PowerModels.jl (or, optionally, `pypowsybl`), and
writes the results as partitioned Parquet files with a fixed, documented
schema.

## 2. Installation and CLI

Installed as a normal Python package (`pip install gridfm-datakit`, or `uv`)
plus a one-time Julia setup:

```bash
gridfm_datakit setup_pm
```

This installs `Ipopt`, `PowerModels`, and `Memento` into the Julia project
pinned by `gridfm_datakit/juliapkg.json` (`PowerModels==0.21.6`,
`Ipopt==1.15.0`, `Memento==1.5.0`; `juliacall` resolves this automatically on
first import too). Julia itself must already be installed separately.

The CLI (`gridfm_datakit/cli.py`) exposes five subcommands:

| Command | Purpose |
| --- | --- |
| `gridfm_datakit generate <config.yaml>` | Run data generation from a config file |
| `gridfm_datakit validate <data_path> [--n-partitions N] [--mode pf\|opf] [--sn-mva V]` | Check generated data for physical/schema consistency |
| `gridfm_datakit stats <data_path> [--sn-mva V] [--n-partitions N]` | Print summary statistics over generated data |
| `gridfm_datakit plots <data_path> [--output-dir DIR] [--sn-mva V] [--n-partitions N]` | Render per-feature violin-style distribution plots for bus data |
| `gridfm_datakit setup_pm` | Install the pinned Julia packages |

`--n-partitions 0` means "use all partitions" for `validate`, `stats`, and
`plots`; the default is 100. `validate --mode` is optional — if omitted, the
mode is read back out of the `args.log` file written during generation.

There is also a Jupyter-based interactive interface (`interactive.py`,
requires the base install — `ipywidgets`, `ipyfilechooser`, `nbformat` are
core dependencies, not gated behind an extra):

```python
from gridfm_datakit.interactive import interactive_interface
interactive_interface()
```

This renders a widget UI covering every config option below (including a
dropdown of all 61 bundled PGLib case names) and can either write a YAML
config file or write-and-run it directly.

## 3. Programmatic API

Besides the CLI, `gridfm_datakit.generate` exposes two entry points, both
accepting a config as a **YAML file path, a plain dict, or a
`NestedNamespace`**:

- `generate_power_flow_data(config)` — sequential, single-process. Simpler,
  used for debugging; no `num_processes`/chunking involved.
- `generate_power_flow_data_distributed(config)` — the one the CLI uses.
  Splits scenarios into `large_chunk_size`-sized chunks, and each chunk
  across `num_processes` workers (via a spawn-context `multiprocessing.Pool`,
  one pool per chunk). Progress is reported through a `Manager().Queue()`.

## 4. Config file structure

A config has five top-level sections: `network`, `load`,
`topology_perturbation`, `generation_perturbation`, `admittance_perturbation`,
and `settings`. Every `*_perturbation` block has a `type` field; passing
extra keys that a given `type` doesn't use produces a `UserWarning` (this is
how the n_minus_k-ignores-`n_topology_variants` behavior below surfaces).

### 4.1 `network`

| Key | Values | Notes |
| --- | --- | --- |
| `name` | grid name, no extension | For `pglib`: one of 61 bundled PGLib case names (`case3_lmbd` through `case78484_epigrids`; see `interactive.py` for the full list). For `file`: filename stem under `network_dir`. |
| `source` | `pglib` \| `file` | `pglib` downloads `pglib_opf_{name}.m` from `raw.githubusercontent.com/power-grid-lib/pglib-opf` on first use and caches it in the installed package directory (`gridfm_datakit/grids/`). `file` loads a local `.m` file from `network_dir/{name}.m`. |
| `network_dir` | path | Only used when `source: file`. |
| `reader` | `native` \| `powsybl` | **Undocumented in README.** Controls how the `.m` file is parsed. `native` (default) uses `matpowercaseframes`. `powsybl` parses via `pypowsybl` (requires the `powsybl` extra) and additionally keeps a live PowSyBl network object around for later use by `pf_solver: powsybl`. |

Every network file, regardless of source, is first run through
`correct_network()`: a round-trip through Julia's
`PowerModels.parse_file` → `PowerModels.export_matpower`, cached next to the
original as `{name}_corrected.m`. This is why running against `scripts/grids/`
leaves a `*_corrected.m` file behind.

`Network` (in `network.py`) enforces several structural invariants on load:
exactly one reference (slack) bus, all generator buses must exist in the bus
table, all generator cost rows must be polynomial (`MODEL == POLYNOMIAL`)
and share the same number of cost coefficients, and the network must form a
single connected component.

### 4.2 `load`

Controls how many demand scenarios are generated and how. `generator` selects
between two independent implementations (`perturbations/load_perturbation.py`):

**`agg_load_profile`** (the documented/default one) — scales the base case's
nominal per-bus load by a time-varying global reference curve, then adds
independent per-bus multiplicative noise. Full parameter set:

| Key | Meaning |
| --- | --- |
| `agg_profile` | Name of a CSV under `gridfm_datakit/load_profiles/`: `default`, or one of nine ERCOT 2024 hourly regional profiles (`ercot_load_act_hr_2024_{total,coast,east,far_west,north,north_central,south_central,southern,west}`). |
| `scenarios` | Number of scenarios `K` to generate. If `K` ≤ profile length (8760 hourly points), the profile is truncated; if larger, it's linearly interpolated up to `K` points. |
| `sigma` | Per-bus multiplicative noise range: each load's factor is drawn `~U(1-sigma, 1+sigma)` independently per bus and scenario. |
| `change_reactive_power` | If true, reactive power gets independent noise+scaling too; if false, Q stays at the nominal case value for every scenario. |
| `start_scaling_factor`, `step_size`, `max_scaling_factor` | Before generating scenarios, the library **runs a real OPF search**: starting at `start_scaling_factor`, it scales all loads by `u`, increments by `step_size`, and re-solves OPF until it fails to converge or `u` exceeds `max_scaling_factor`. The last convergent `u` becomes the upper bound of the reference curve. **This means even a "PF mode, no generator perturbation" run does at least one real OPF solve before any scenario is generated.** |
| `global_range` | Sets the reference curve's lower bound as `l = u - global_range * u` (not `u * (1 - global_range)` — see the code comment in `load_perturbation.py` noting this was a deliberate change from a prior formula). |

Mathematically, for load `i`, scenario `k`: `p̃ᵢᵏ = pᵢ · ref(k) · εᵢᵏ` where
`ref(k)` is the aggregate profile min-max scaled to `[l, u]` and
`εᵢᵏ ~ U(1-σ, 1+σ)`.

**`powergraph`** — much simpler: `ref(k) = agg(k) / max(agg)`, no OPF search,
no per-bus noise, reactive power always held fixed at nominal. Only
`agg_profile` is consulted; any other `load.*` key triggers the "unused
arguments" warning.

### 4.3 `topology_perturbation`

Three `type` values (`perturbations/topology_perturbation.py`):

- **`none`** — yields the unperturbed network once (`NoPerturbationGenerator`).
- **`random`** (`RandomComponentDropGenerator`) — samples
  `n_topology_variants` feasible topologies per load scenario. Each sample
  picks a count of outages `r` (uniform over `1..k` by default, or from an
  explicit `outage_count_probabilities` distribution over `0..k` — a
  probability vector or `{count: probability}` mapping that must sum to 1)
  and drops `r` random components from `elements` (`branch`, `gen`, or both;
  default is both). A topology is kept only if the resulting network is
  still a single connected component; infeasible draws are retried up to
  `max(500, 50 * n_topology_variants)` times before raising `RuntimeError`.
  Dropping a generator that leaves a PV bus with no active generator demotes
  that bus to PQ automatically (`Network.deactivate_gens`).
- **`n_minus_k`** (`NMinusKGenerator`) — **exhaustively enumerates every
  combination of up to `k` branches/transformers** taken out of service
  (only branches — never generators — and only up to the number of
  in-service branches choose `k`), filters to the feasible (single connected
  component) ones, and yields all of them, once, per load scenario. It
  **ignores `n_topology_variants`, `elements`, and `outage_count_probabilities`
  entirely** and warns if they're set. This means it is not a "sampling
  strategy" in the same family as `random` — it's a fixed, deterministic,
  and potentially much larger dataset per load scenario (see the
  `random` vs `n_minus_k` experiment in `GridFM_documentation.md`: 5 sampled
  vs 38 exhaustive topologies on `case24_ieee_rts` with `k=1`). `k > 1` prints
  a performance warning since the combination count grows combinatorially.

### 4.4 `generation_perturbation`

Perturbs generator cost polynomial coefficients
(`perturbations/generator_perturbation.py`). In all cases, generators whose
cost is **constant-only** (all coefficients zero except `c0`) are always
left untouched — this is asserted by validation
(`validate_constant_cost_generators_unchanged`).

- **`none`** — unperturbed (`NoGenPerturbationGenerator`).
- **`cost_permutation`** (`PermuteGenCostGenerator`) — randomly permutes the
  full cost-coefficient rows *among* the permutable generators (those with a
  non-zero linear or quadratic term). No extra parameters; a `sigma` key
  here is unused and warns.
- **`cost_perturbation`** (`PerturbGenCostGenerator`, requires `sigma`) —
  multiplies each permutable generator's cost coefficients by an independent
  factor `~U(max(0, 1-sigma), 1+sigma)`.

### 4.5 `admittance_perturbation`

Perturbs line/transformer `R` and `X` (`perturbations/admittance_perturbation.py`).

- **`none`** — unperturbed.
- **`random_perturbation`** (requires `sigma`) — for every branch
  independently, `R' ~ U(l·R, u·R)` and `X' ~ U(l·X, u·X)` where
  `l = max(0, 1-sigma)`, `u = 1+sigma`. (Line charging susceptance `B` is
  *not* perturbed — noted as a `TODO` in the source.)

Confirmed empirically: raising `sigma` from 0.05 to 0.8 roughly tripled the
Y-bus conductance (`G`) standard deviation and nearly doubled the branch
overload count on the same load/topology scenarios (see
`GridFM_documentation.md`).

### 4.6 `settings`

| Key | Meaning |
| --- | --- |
| `num_processes` | Worker count for distributed generation. |
| `data_dir` | Output root; final path is `{data_dir}/{network.name}/raw/`. |
| `large_chunk_size` | Scenarios per outer chunk; each chunk is saved to disk before the next starts (bounds peak memory). |
| `overwrite` | If true, wipes and recreates the output dir; if false, appends. |
| `mode` | `pf` \| `opf` — see §5. |
| `include_dc_res` | Also solve and store DC PF/OPF results alongside AC. |
| `enable_solver_logs` | Write per-solver-call logs under `{data_dir}/.../raw/solver_log/`. Fast PF/DCPF paths never log regardless. |
| `pf_solver` | **Undocumented in README.** `powermodel` (default) \| `powsybl`. Selects the engine used for the post-perturbation PF solve in PF mode (see §6). OPF is *always* solved via PowerModels regardless of this setting. |
| `pf_fast` | Use PowerModels' direct `compute_ac_pf` instead of the Ipopt-optimizer-based AC PF. Faster and (per the README) more accurate, but doesn't converge on some large networks (e.g. `case10000_goc`). Only consulted when `pf_solver: powermodel`. |
| `dcpf_fast` | Same, for DC PF (`compute_dc_pf`). |
| `max_iter` | Max Ipopt iterations for AC OPF/PF. |
| `seed` | If set, used for reproducible scenario generation (all other config values must also match to get identical output). If null, a fresh random seed is generated and printed. |

Two settings not exposed in the config schema at all: the interactive UI's
`num_processes` slider caps at 32; `dc_max_iter` for DC OPF defaults to 1000
and currently has no config surface (only reachable by calling
`init_julia()` directly).

## 5. PF mode vs OPF mode

This is the central mode switch, and the two modes apply perturbations in a
**different order** (`process/process_network.py`):

- **`pf` mode** (`process_scenario_pf_mode`): generation-cost and admittance
  perturbations are applied, then **OPF is solved first** (on the
  unperturbed topology) to get feasible generator setpoints, *then* topology
  perturbations are applied on top of that fixed dispatch, and PF (not OPF)
  is solved on each resulting topology. Because the dispatch isn't
  re-optimized for the new topology, this can — and, per our experiments,
  does — produce operating-limit violations (branch overloads, voltage
  excursions). This is intentional: it's how the library generates the
  "out-of-operating-limits" scenarios the README advertises. A topology or
  load combination whose *initial* OPF fails to converge is dropped
  entirely and logged to `error.log`; at 2000+ bus scale we measured roughly
  a 15% drop rate.
- **`opf` mode** (`process_scenario_opf_mode`): topology, then generation,
  then admittance perturbations are all applied *before* solving OPF, so the
  dispatch is always re-optimized for the perturbed grid. Every yielded
  scenario is by construction feasible (no overloads); scenarios where OPF
  itself fails to converge are dropped and logged. This is far slower per
  scenario (in our test, ~20–30x the AC solve time of PF mode on the same
  grid) because it's solving a full nonlinear OPF for every single
  topology/generation/admittance combination, not just once per load
  scenario.

## 6. Solver engines

Two independent solver axes:

- **OPF**: always PowerModels.jl / Ipopt (`solve_ac_opf`, `solve_dc_opf`).
  Not configurable.
- **PF** (only relevant in `pf` mode, for the post-perturbation solve):
  `settings.pf_solver` chooses between:
  - `powermodel` (default): either `compute_ac_pf`/`compute_dc_pf`
    (`pf_fast`/`dcpf_fast: true`, direct computation, faster) or
    `solve_ac_pf`/`solve_dc_pf` via Ipopt (`false`, slower, sometimes needed
    for large/ill-conditioned networks).
  - `powsybl`: solves via `pypowsybl.loadflow.run_ac`/`run_dc` instead,
    using PowSyBl's variant-cloning mechanism to apply each perturbation
    without touching the base network. Requires `network.reader: powsybl`
    (to get a live `pypowsybl` network object) and the `powsybl` extra
    (`pip install gridfm-datakit[powsybl]`); using `pf_solver: powsybl`
    without it raises `ImportError` with that install hint.

`init_julia()` also warms up every entry point (opf, dcopf, pf, pf_fast,
dcpf, dcpf_fast) once at startup against a bundled dummy case, specifically
so Ipopt's one-time license banner and Julia's JIT warm-up land during
initialization rather than mid-run.

## 7. Output files and schema

Written under `{data_dir}/{network.name}/raw/`:

| File | Content |
| --- | --- |
| `bus_data.parquet` | Per-scenario, per-bus features (partitioned) |
| `branch_data.parquet` | Per-scenario, per-branch features (partitioned) |
| `gen_data.parquet` | Per-scenario, per-generator features (partitioned) |
| `y_bus_data.parquet` | Nonzero Y-bus entries: `[scenario, index1, index2, G, B]` (partitioned) |
| `runtime_data.parquet` | AC (and DC) solve time per scenario (partitioned) |
| `scenarios_{generator}.parquet` | The raw load scenarios (`p_mw`, `q_mvar` per load/bus/scenario) |
| `scenarios_{generator}.html` | Plotly plot of load scenarios — only generated if the network has ≤100 buses |
| `scenarios_{generator}.log` | The `u`/`l` bounds found for `agg_load_profile`, or generator-specific notes |
| `args.log` | YAML dump of the exact config used |
| `tqdm.log`, `error.log` | Progress and per-scenario error records |
| `solver_log/` | Per-solver-call logs, only if `enable_solver_logs: true` |

The four main tables are **Hive-partitioned by `scenario_partition`**, 200
scenarios per partition (`n_scenario_per_partition = 200` in
`utils/utils.py`) — this is why our 250-scenario smoke test produced
`scenario_partition=0` and `scenario_partition=1` subdirectories.

Columns (`utils/column_names.py`):

- **`BUS_COLUMNS`**: `bus, Pd, Qd, Pg, Qg, Vm, Va, PQ, PV, REF, vn_kv, min_vm_pu, max_vm_pu, GS, BS` (plus `load_scenario_idx`). `PQ`/`PV`/`REF` are one-hot bus-type flags. `+DC_BUS_COLUMNS`: `Va_dc, Pg_dc` when `include_dc_res: true`.
- **`GEN_COLUMNS`**: `idx, bus, p_mw, q_mvar, min_p_mw, max_p_mw, min_q_mvar, max_q_mvar, cp0_eur, cp1_eur_per_mw, cp2_eur_per_mw2, in_service, is_slack_gen`. `+DC_GEN_COLUMNS`: `p_mw_dc`.
- **`BRANCH_COLUMNS`**: `idx, from_bus, to_bus, pf, qf, pt, qt, r, x, b, Yff_r, Yff_i, Yft_r, Yft_i, Ytf_r, Ytf_i, Ytt_r, Ytt_i, tap, shift, ang_min, ang_max, rate_a, br_status`. `+DC_BRANCH_COLUMNS`: `pf_dc, pt_dc`.
- **`YBUS_COLUMNS`**: `index1, index2, G, B`.
- **`RUNTIME_COLUMNS`**: `ac`. `+DC_RUNTIME_COLUMNS`: `dc`.

Deactivated branches/generators still get a row (with `br_status`/`in_service
= 0` and zeroed flow/output columns), so shapes are consistent across
scenarios with different topologies.

## 8. Validation

`gridfm_datakit validate` (`validation.py`) runs a fixed sequence of checks
against sampled (or all) partitions, all vectorized over pandas. This is
the full list, in the order they run:

1. Scenario-indexing consistency across all four tables
2. Bus-indexing consistency (branch/gen buses ⊆ bus table)
3. Data completeness — required columns present, no NaNs, tables non-empty
4. DC-columns consistency — if any DC column is NaN for a scenario, all DC
   columns must be NaN for that scenario (i.e. a DC solve either fully
   succeeded or fully failed, no partial state)
5. Voltage angles within `[-180, 180]°` (AC and DC)
6. Y-bus diagonal consistency vs. bus shunt (`GS`/`BS`) + summed branch
   admittances
7. Deactivated branches have zero flow and zero admittance entries
8. Admittance calculations (`Yff`/`Yft`/`Ytf`/`Ytt`) match the `r/x/b/tap/shift` formulas
9. Computed-from-Vm/Va power flows match the stored `pf/qf/pt/qt`
10. Transformer tap ratio is never zero for active branches
11. Branch loading limits — **asserts ≤1.01 p.u. in OPF mode; in PF mode
    only computes and reports statistics** (binding-constraint and overload
    counts), since PF mode is expected to allow violations
12. Deactivated generators have zero output
13. Generator P (and, in OPF mode, Q) limits respected, with binding-limit
    counts reported
14. OPF-mode only: voltage magnitude within `[min_vm_pu, max_vm_pu]`
15. OPF-mode only: branch angle-difference within `[ang_min, ang_max]`
    (branches with `ang_min == ang_max == 0` are treated as unbounded, per
    MATPOWER convention, not as a hard 0 constraint)
16. Bus `Pg`/`Qg` equal the sum of connected in-service generator output
17. Bus `Pg_dc` equals the sum of DC generator output (if DC data present)
18. PF-mode only: `Pg == Pg_dc` at every **non-slack** bus (the slack bus is
    allowed to differ, since it absorbs the AC/DC balance mismatch)
19. Power balance (Kirchhoff's current law) holds at every bus
20. Constant-cost generators' cost coefficients never change across scenarios
21. Bus-type/generator consistency: PV buses have ≥1 active generator, PQ
    buses have none, REF buses have ≥1

Any failure raises `AssertionError` with the offending scenario/bus/branch
identified; the CLI catches this and exits non-zero.

## 9. Stats and plots

- `gridfm_datakit stats` (`utils/stats.py: plot_stats`) computes and prints
  summary statistics (ranges, distributions) over bus/branch/gen data,
  scaled by `--sn-mva`.
- `gridfm_datakit plots` (`plot_feature_distributions`) renders violin-style
  distribution plots for every bus feature, one file per feature, under
  `{data_path}/feature_plots/` by default.

Both accept `--n-partitions` (0 = all) to control how much of a large
dataset gets loaded into memory for the computation.

## 10. Optional extras (`pyproject.toml`)

| Extra | Adds | Needed for |
| --- | --- | --- |
| `test` | `pytest`, `pytest-cov`, `pyinstrument`, `pytest-xdist` | Running the test suite |
| `dev` | `mkdocs`, `mkdocs-material`, `mkdocstrings[python]`, `pre-commit`, `bandit`, `build` | Docs build, linting, packaging |
| `powsybl` | `pypowsybl` | `network.reader: powsybl` and `settings.pf_solver: powsybl` |

Base install already includes the full interactive-UI stack
(`ipykernel`, `ipywidgets`, `ipyfilechooser`, `nbformat`) and plotting stack
(`plotly`, `matplotlib`) unconditionally — these are not gated behind an
extra despite being unnecessary for headless data generation (also flagged
as a dependency-hygiene finding in `docs/improvements/gridfm-datakit-review.md`).

## 11. Dataset converters (`pfdelta/`, `opf_data/`)

These are standalone scripts, separate from the `gridfm_datakit` package and
the `generate`/`validate`/`stats`/`plots` CLI — they don't generate new
scenarios, they **normalize third-party datasets into this library's own
schema** so they can be validated and compared against `gridfm-datakit`
output on equal footing (see the comparison notebooks in §12).

- **`opf_data/batch_convert.py`** — converts OPFData-style OPF result JSON
  files (`example*.json`, searched recursively) into the same
  `bus_data`/`branch_data`/`gen_data`/`y_bus_data` partitioned-parquet schema
  used by `generate`.

  ```bash
  python opf_data/batch_convert.py /path/to/opf_data/ /path/to/output/ [--chunk-size 2000]
  ```

- **`pfdelta/batch_convert_pfdelta.py`** — same idea for PF-Delta-style
  PowerModels/PGLib solution JSON (`sample_N.json`; scenario index = `N-1`).

  ```bash
  python pfdelta/batch_convert_pfdelta.py --data-dir /path/to/raw/ --out-dir /path/to/converted/ [--chunk-size 2000]
  ```

Both process files in fixed-size chunks with multiprocessing, append
incrementally to keep memory bounded, partition output at 100 scenarios per
partition (note: **not** the 200-scenario partitioning `generate` uses — see
§7), recompute the Y-bus admittance matrix from branch parameters via the
same `compute_branch_admittances()` used by validation (rather than trusting
whatever the source JSON stored), and assert a set of physical invariants
about the source data on the way in (single slack bus, non-zero branch
reactance, generator cost matching the solution objective within `1e-3`,
etc. — see each tool's `README.md` for the full list). Output is directly
consumable by `gridfm_datakit validate`.

## 12. Utility / dev scripts (`scripts/`)

Not part of the installed package or its public API, but shipped in the
repo and useful when working on datasets generated by this library:

| Script | Purpose |
| --- | --- |
| `scripts/compare_parquet_files.py` | Diffs two directories of generated parquet output column-by-column — for checking that a code change didn't silently change the dataset. |
| `scripts/convert_to_partitioned_parquet.py <data_dir>` | Migrates old, non-partitioned parquet output into the current partitioned format. |
| `scripts/parse_ipopt_logs.py` | Fast (no-regex, streaming, memory-mapped) parser for Ipopt solver logs — extracts iteration counts and exit messages, for when `settings.enable_solver_logs: true` was used on a large run. |
| `scripts/summary_data_gen.py` | Builds a summary table over a batch of generation runs by reading each run's `args.log` and its Ipopt logs (via `parse_ipopt_logs`). |
| `scripts/debug.py` | Minimal repro harness: loads `scripts/config/default.yaml`, overrides it to 32 scenarios into `debug_data/`, and runs generation directly (no CLI) for debugging in a Python debugger. |
| `scripts/interactive_interface.ipynb` | Notebook wrapper around `interactive_interface()` (§2). |

Three comparison notebooks under `scripts/notebooks/` (used for benchmarking
against competing tools, not part of the package):

- `comparison_opf.ipynb` — loads PF-Delta `.mat` output, PGLearn CSV output,
  OPFData CSV output, and multiple `gridfm-datakit` runs side by side for
  direct comparison.
- `comparison_perturbations.ipynb` — compares several `gridfm-datakit` runs
  generated with different perturbation settings (e.g. `k`, `sigma`, step
  size) against each other and against PF-Delta.
- `dispatch_with_powermodels.ipynb` — walks through the low-level
  `load_net_from_pglib` → `init_julia` → `pf_preprocessing`/`pf_post_processing`
  call sequence that `generate.py` wraps, useful as a worked example of the
  internal API.

## 13. Known scale characteristics (measured, not just documented)

From local experiments (`GridFM_documentation.md` has full detail and repo
configs under `scripts/config/smoke_test*.yaml`):

- On a 24-bus grid (`case24_ieee_rts`), AC PF solves in ~0.7ms, AC OPF in
  ~21ms.
- On a 2000-bus grid (Texas2k), AC PF is ~69ms and AC OPF-based dispatch
  search occasionally fails to converge — about 15% of base load scenarios
  were dropped with `OPF did not converge: ITERATION_LIMIT` in our test,
  even though the run was in `pf` mode (recall PF mode still runs one OPF
  per scenario to get a base dispatch).
- `n_minus_k` topology perturbation produces roughly 7-8x more
  scenario-partitions than `random` with 5 variants, for the same load
  scenario count, on a 24-bus grid — this ratio will differ substantially on
  larger grids since the number of N-1 candidates grows with branch count.
