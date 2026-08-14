#!/usr/bin/env python3
"""Generate the config files + manifest for the overnight batch dataset run.

Writes one YAML config per dataset under scripts/config/overnight/, plus a
manifest.json (dataset name -> purpose/task/grid/mode) used by run_all.sh to
drive generation sequentially and by GridFM_documentation.md write-up later.
"""

import json
import os
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "scripts" / "config" / "overnight"
DATA_ROOT = "./data_out/overnight"
SEED = 42
NUM_PROCESSES = 32


def base_config(
    network_name: str,
    mode: str,
    scenarios: int,
    dataset_name: str,
    *,
    topology_type: str = "random",
    k: int = 1,
    n_topology_variants: int = 5,
    elements=None,
    outage_count_probabilities=None,
    generation_type: str = "cost_permutation",
    generation_sigma: float = 1.0,
    admittance_type: str = "random_perturbation",
    admittance_sigma: float = 0.2,
    sigma: float = 0.2,
    global_range: float = 0.4,
    max_scaling_factor: float = 4.0,
    step_size: float = 0.1,
    start_scaling_factor: float = 1.0,
    pf_fast: bool = True,
    dcpf_fast: bool = True,
    enable_solver_logs: bool = False,
    large_chunk_size: int = 500,
) -> dict:
    elements = elements or ["branch", "gen"]
    topo = {
        "type": topology_type,
        "k": k,
        "n_topology_variants": n_topology_variants,
        "elements": elements,
    }
    if outage_count_probabilities is not None:
        topo["outage_count_probabilities"] = outage_count_probabilities

    cfg = {
        "network": {
            "name": network_name,
            "source": "pglib",
            "network_dir": "scripts/grids",
        },
        "load": {
            "generator": "agg_load_profile",
            "agg_profile": "default",
            "scenarios": scenarios,
            "sigma": sigma,
            "change_reactive_power": True,
            "global_range": global_range,
            "max_scaling_factor": max_scaling_factor,
            "step_size": step_size,
            "start_scaling_factor": start_scaling_factor,
        },
        "topology_perturbation": topo,
        "generation_perturbation": {
            "type": generation_type,
            "sigma": generation_sigma,
        },
        "admittance_perturbation": {
            "type": admittance_type,
            "sigma": admittance_sigma,
        },
        "settings": {
            "num_processes": NUM_PROCESSES,
            "data_dir": f"{DATA_ROOT}/{dataset_name}",
            "large_chunk_size": min(large_chunk_size, scenarios),
            "overwrite": True,
            "mode": mode,
            "include_dc_res": True,
            "enable_solver_logs": enable_solver_logs,
            "pf_fast": pf_fast,
            "dcpf_fast": dcpf_fast,
            "max_iter": 200,
            "seed": SEED,
        },
    }
    return cfg


# (name, task/purpose, config dict)
DATASETS = []


def add(name: str, purpose: str, cfg: dict) -> None:
    DATASETS.append({"name": name, "purpose": purpose, "config": cfg})


# --- Group 1: PF baseline (PowerFlow task) ---
add(
    "pf_small_case14",
    "PowerFlow task baseline (small grid)",
    base_config("case14_ieee", "pf", 3000, "pf_small_case14", n_topology_variants=5),
)
add(
    "pf_medium_case118",
    "PowerFlow task baseline (medium grid)",
    base_config(
        "case118_ieee",
        "pf",
        2000,
        "pf_medium_case118",
        n_topology_variants=5,
    ),
)
add(
    "pf_large_case2000",
    "PowerFlow task baseline (large grid)",
    base_config(
        "case2000_goc",
        "pf",
        1000,
        "pf_large_case2000",
        n_topology_variants=3,
        pf_fast=False,
    ),
)

# --- Group 2: OPF baseline (OptimalPowerFlow task) ---
add(
    "opf_small_case24",
    "OptimalPowerFlow task baseline (small grid)",
    base_config(
        "case24_ieee_rts",
        "opf",
        1000,
        "opf_small_case24",
        n_topology_variants=3,
    ),
)
add(
    "opf_medium_case118",
    "OptimalPowerFlow task baseline (medium grid)",
    base_config(
        "case118_ieee",
        "opf",
        400,
        "opf_medium_case118",
        n_topology_variants=3,
    ),
)
add(
    "opf_large_case500",
    "OptimalPowerFlow task baseline (large grid)",
    base_config(
        "case500_goc",
        "opf",
        150,
        "opf_large_case500",
        n_topology_variants=2,
    ),
)

# --- Group 3: Contingency exhaustive (n_minus_k) -- topology ID / security screening ---
add(
    "contingency_small_case24",
    "Exhaustive N-1 contingency screening / topology identification (small grid)",
    base_config(
        "case24_ieee_rts",
        "pf",
        500,
        "contingency_small_case24",
        topology_type="n_minus_k",
        k=1,
    ),
)
add(
    "contingency_medium_case118",
    "Exhaustive N-1 contingency screening / topology identification (medium grid)",
    base_config(
        "case118_ieee",
        "pf",
        300,
        "contingency_medium_case118",
        topology_type="n_minus_k",
        k=1,
    ),
)
add(
    "contingency_large_case2000",
    "Exhaustive N-1 contingency screening / topology identification (large grid)",
    base_config(
        "case2000_goc",
        "pf",
        50,
        "contingency_large_case2000",
        topology_type="n_minus_k",
        k=1,
        # pf_fast=True here: exhaustive n_minus_k multiplies the per-solve cost
        # by branches-in-service (3634 for case2000_goc), so the slow
        # Ipopt-based PF path turns this into a multi-hour job. Confirmed
        # live: with pf_fast=False, 32 workers at 99% CPU still produced zero
        # completed scenarios after 38 minutes.
    ),
)

# --- Group 4: Line parameter estimation -- fixed topology, wide admittance sweep ---
add(
    "line_param_small_case24",
    "Line R/X parameter estimation from flows (fixed topology, wide admittance sweep, small grid)",
    base_config(
        "case24_ieee_rts",
        "pf",
        3000,
        "line_param_small_case24",
        topology_type="none",
        admittance_sigma=1.5,
    ),
)
add(
    "line_param_medium_case118",
    "Line R/X parameter estimation from flows (fixed topology, wide admittance sweep, medium grid)",
    base_config(
        "case118_ieee",
        "pf",
        2000,
        "line_param_medium_case118",
        topology_type="none",
        admittance_sigma=1.5,
    ),
)

# --- Group 5: Solver difficulty / runtime prediction -- span sizes, real Ipopt logs ---
_SOLVER_DIFF_GRIDS = [
    "case14_ieee",
    "case24_ieee_rts",
    "case57_ieee",
    "case118_ieee",
    "case300_ieee",
    "case500_goc",
    "case2000_goc",
]
for grid in _SOLVER_DIFF_GRIDS:
    name = f"solver_difficulty_{grid}"
    add(
        name,
        f"Solver runtime/convergence-difficulty prediction ({grid})",
        base_config(
            grid,
            "pf",
            300,
            name,
            n_topology_variants=3,
            pf_fast=False,
            dcpf_fast=False,
            enable_solver_logs=True,
        ),
    )

# --- Group 6: Loadability boundary -- infeasibility / loadability-limit labels ---
_LOADABILITY_GRIDS = ["case57_ieee", "case300_ieee", "case2000_goc"]
for grid in _LOADABILITY_GRIDS:
    name = f"loadability_{grid}"
    add(
        name,
        f"Loadability-limit / infeasibility-boundary labels ({grid}; see error.log + scenarios_*.log for boundary points)",
        base_config(
            grid,
            "pf",
            500,
            name,
            sigma=0.35,
            pf_fast=grid != "case2000_goc",
        ),
    )

# --- Group 7: Cost-regime sweep -- generalization across cost distributions ---
for cost_sigma in [0.2, 1.0, 2.5]:
    name = f"cost_sweep_sigma{cost_sigma}"
    add(
        name,
        f"Cost-distribution generalization (OPF, cost_perturbation sigma={cost_sigma})",
        base_config(
            "case57_ieee",
            "opf",
            500,
            name,
            n_topology_variants=2,
            generation_type="cost_perturbation",
            generation_sigma=cost_sigma,
        ),
    )

# --- Group 8: Cross-grid generalization -- same config across many grid sizes ---
_CROSSGRID_GRIDS = [
    "case14_ieee",
    "case24_ieee_rts",
    "case57_ieee",
    "case118_ieee",
    "case300_ieee",
    "case500_goc",
    "case2000_goc",
]
for grid in _CROSSGRID_GRIDS:
    name = f"crossgrid_{grid}"
    add(
        name,
        f"Cross-grid-size generalization, identical perturbation config ({grid})",
        base_config(
            grid,
            "pf",
            800,
            name,
            n_topology_variants=5,
            pf_fast=grid != "case2000_goc",
        ),
    )


def main() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for ds in DATASETS:
        config_path = CONFIG_DIR / f"{ds['name']}.yaml"
        with open(config_path, "w") as f:
            yaml.safe_dump(ds["config"], f, sort_keys=False)
        manifest.append(
            {
                "name": ds["name"],
                "purpose": ds["purpose"],
                "config_path": os.path.relpath(config_path, REPO_ROOT),
                "network": ds["config"]["network"]["name"],
                "mode": ds["config"]["settings"]["mode"],
                "scenarios": ds["config"]["load"]["scenarios"],
                "status": "pending",
            },
        )

    manifest_path = CONFIG_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Wrote {len(manifest)} configs to {CONFIG_DIR}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
