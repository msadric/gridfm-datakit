#!/usr/bin/env python3
"""Sequentially run every config in the overnight-batch manifest.

Runs `gridfm_datakit generate` for each dataset one at a time (so each gets
the full machine), logs stdout/stderr per dataset under
scripts/config/overnight/logs/, and updates manifest.json's status field
after each one so progress can be checked mid-run. A failure in one dataset
does not stop the batch; it's recorded and the run moves to the next.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "scripts" / "config" / "overnight"
LOG_DIR = CONFIG_DIR / "logs"
MANIFEST_PATH = CONFIG_DIR / "manifest.json"


def load_manifest() -> list:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def save_manifest(manifest: list) -> None:
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()

    batch_start = time.time()
    print(f"Starting overnight batch: {len(manifest)} datasets")

    for i, entry in enumerate(manifest):
        if entry.get("status") == "done":
            print(f"[{i + 1}/{len(manifest)}] {entry['name']}: already done, skipping")
            continue

        name = entry["name"]
        config_path = REPO_ROOT / entry["config_path"]
        log_path = LOG_DIR / f"{name}.log"

        print(
            f"\n[{i + 1}/{len(manifest)}] {name} ({entry['network']}, "
            f"{entry['mode']}, {entry['scenarios']} scenarios) -> {log_path}",
        )
        entry["status"] = "running"
        entry["started_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_manifest(manifest)

        start = time.time()
        with open(log_path, "w") as log_file:
            result = subprocess.run(
                [
                    str(REPO_ROOT / ".venv" / "bin" / "gridfm_datakit"),
                    "generate",
                    str(config_path),
                ],
                cwd=str(REPO_ROOT),
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
        elapsed = time.time() - start

        entry["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        entry["elapsed_seconds"] = round(elapsed, 1)
        entry["status"] = "done" if result.returncode == 0 else "failed"
        entry["returncode"] = result.returncode
        save_manifest(manifest)

        status_word = "OK" if result.returncode == 0 else "FAILED"
        print(f"  -> {status_word} in {elapsed:.1f}s (see {log_path})")

    total_elapsed = time.time() - batch_start
    n_done = sum(1 for e in manifest if e["status"] == "done")
    n_failed = sum(1 for e in manifest if e["status"] == "failed")
    print(
        f"\nBatch complete in {total_elapsed / 3600:.2f}h: "
        f"{n_done} done, {n_failed} failed, {len(manifest)} total",
    )
    sys.exit(1 if n_failed else 0)


if __name__ == "__main__":
    main()
