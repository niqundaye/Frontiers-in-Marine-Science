from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd
import yaml

from fishery_repro.integrity import content_for_hash, sha256_file


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ARTIFACT_MANIFEST.csv"
SMOKE_CONFIG = ROOT / "configs" / "experiments" / "ci_smoke.yaml"


def verify_manifest() -> dict[str, int]:
    missing: list[str] = []
    mismatched: list[str] = []
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        relative = row["path"]
        target = ROOT / relative
        if not target.is_file():
            missing.append(relative)
        else:
            mode = row.get("hash_mode") or None
            if sha256_file(target, mode) != row["sha256"]:
                mismatched.append(relative)
            elif len(content_for_hash(target, mode)) != int(row["bytes"]):
                mismatched.append(f"{relative} (canonical byte count)")
    if missing or mismatched:
        detail = {
            "missing": missing[:20],
            "mismatched": mismatched[:20],
            "missing_count": len(missing),
            "mismatched_count": len(mismatched),
        }
        raise RuntimeError(f"Artifact manifest verification failed: {json.dumps(detail)}")
    return {"verified_files": len(rows), "missing": 0, "mismatched": 0}


def run(*arguments: str) -> None:
    command = [sys.executable, *arguments]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def validate_smoke_output(output_root: Path) -> dict[str, int]:
    experiment_dir = output_root / "experiments" / "ci_smoke"
    config = yaml.safe_load(SMOKE_CONFIG.read_text(encoding="utf-8"))
    expected_runs = len(config["algorithms"]) * len(config["seeds"])
    expected_generations = expected_runs * int(config["generations"])

    run_summary = pd.read_csv(experiment_dir / "run_summary.csv")
    generation_log = pd.read_csv(experiment_dir / "generation_log.csv")
    objectives = pd.read_csv(experiment_dir / "final_population_objectives_constraints.csv")
    assert len(run_summary) == expected_runs
    assert len(generation_log) == expected_generations
    assert set(run_summary["algorithm"]) == set(config["algorithms"])
    assert objectives["data_status"].str.contains("surrogate").all()
    assert objectives.filter(regex=r"^g_").shape[1] == 7
    return {
        "runs": len(run_summary),
        "generation_records": len(generation_log),
        "final_solutions": len(objectives),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Non-destructive offline reviewer check for integrity, tests and executability."
    )
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    args = parser.parse_args()

    started = time.perf_counter()
    report: dict[str, object] = {
        "schema_version": "1.0",
        "artifact_version": "0.3.0",
        "python": sys.version.split()[0],
        "manifest": verify_manifest(),
    }

    run("scripts/validate_reproducibility_package.py", "--check-only")
    report["package_validation"] = "pass"

    if not args.skip_tests:
        run("-m", "pytest", "-q")
        report["tests"] = "pass"
    else:
        report["tests"] = "skipped"

    if not args.skip_smoke:
        with tempfile.TemporaryDirectory(prefix="fishery_reviewer_") as temporary:
            output_root = Path(temporary) / "results"
            run(
                "-m",
                "fishery_repro",
                "experiment",
                "--experiment-config",
                str(SMOKE_CONFIG),
                "--output-root",
                str(output_root),
            )
            report["smoke_experiment"] = validate_smoke_output(output_root)
    else:
        report["smoke_experiment"] = "skipped"

    report["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    report["status"] = "pass"
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
