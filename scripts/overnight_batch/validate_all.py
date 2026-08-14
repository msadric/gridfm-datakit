#!/usr/bin/env python3
"""Validate every 'done' dataset from the overnight batch manifest.

Runs `gridfm_datakit validate` against each dataset's raw output directory
and prints a pass/fail summary. Does not modify manifest.json.
"""

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "scripts" / "config" / "overnight" / "manifest.json"


def main() -> None:
    manifest = json.load(open(MANIFEST_PATH))
    done = [e for e in manifest if e["status"] == "done"]

    results = []
    for i, entry in enumerate(done):
        name = entry["name"]
        data_path = REPO_ROOT / "data_out" / "overnight" / name / entry["network"] / "raw"
        print(f"\n[{i + 1}/{len(done)}] Validating {name} ({data_path})...")

        result = subprocess.run(
            [
                str(REPO_ROOT / ".venv" / "bin" / "gridfm_datakit"),
                "validate",
                str(data_path),
                "--mode",
                entry["mode"],
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        passed = result.returncode == 0
        results.append({"name": name, "passed": passed, "returncode": result.returncode})
        status_word = "PASS" if passed else "FAIL"
        print(f"  -> {status_word}")
        if not passed:
            print("  --- stdout tail ---")
            print("\n".join(result.stdout.splitlines()[-15:]))
            print("  --- stderr tail ---")
            print("\n".join(result.stderr.splitlines()[-15:]))

    n_pass = sum(1 for r in results if r["passed"])
    n_fail = len(results) - n_pass
    print(f"\n\n=== Validation summary: {n_pass}/{len(results)} passed, {n_fail} failed ===")
    for r in results:
        print(f"  {'PASS' if r['passed'] else 'FAIL'}  {r['name']}")


if __name__ == "__main__":
    main()
