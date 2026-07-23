from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*arguments: str) -> None:
    command = [sys.executable, *arguments]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild data, figures, detailed experiment logs, result bundles and audits."
    )
    parser.add_argument(
        "--experiment-config",
        default="configs/experiments/processed_demo.yaml",
    )
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    run("-m", "fishery_repro", "all")
    run(
        "-m",
        "fishery_repro",
        "experiment",
        "--experiment-config",
        args.experiment_config,
    )
    run("scripts/build_implementation_bundles.py")
    run("scripts/validate_reproducibility_package.py")
    run("scripts/build_artifact_manifest.py")
    if not args.skip_tests:
        run("-m", "pytest")


if __name__ == "__main__":
    main()
