from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_LABELS = ("经过处理的数据", "processed", "surrogate")


def require(condition: bool, message: str, checks: list[dict[str, str]]) -> None:
    checks.append({"check": message, "status": "pass" if condition else "fail"})
    if not condition:
        raise AssertionError(message)


def main() -> None:
    checks: list[dict[str, str]] = []
    for number in range(1, 11):
        bundle = ROOT / "implementations" / f"figure_{number:02d}"
        require((bundle / "analysis.py").exists(), f"Figure {number} has analysis.py", checks)
        require((bundle / "derived_data.csv").exists(), f"Figure {number} has derived data", checks)
        report_path = bundle / "validation_report.json"
        require(report_path.exists(), f"Figure {number} has validation report", checks)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        require(report.get("status") == "pass", f"Figure {number} validation passes", checks)
        require(
            any(label in report.get("data_status", "") for label in PROCESSED_LABELS),
            f"Figure {number} processed-data disclosure",
            checks,
        )

    for number in range(1, 5):
        bundle = ROOT / "implementations" / f"table_{number:02d}"
        require((bundle / "analysis.py").exists(), f"Table {number} has analysis.py", checks)
        report = json.loads((bundle / "validation_report.json").read_text(encoding="utf-8"))
        require(report.get("status") == "pass", f"Table {number} validation passes", checks)

    experiment = ROOT / "results" / "experiments" / "processed_demo"
    required_outputs = {
        "generation_log.csv",
        "reference_relocation_log.csv",
        "final_population_objectives_constraints.csv",
        "final_population_decision_vectors.csv",
        "run_summary.csv",
        "algorithm_summary.csv",
        "run_metadata.json",
        "config_snapshot.yaml",
    }
    for filename in required_outputs:
        require((experiment / filename).exists(), f"Experiment has {filename}", checks)

    if experiment.exists():
        generations = pd.read_csv(experiment / "generation_log.csv")
        runs = pd.read_csv(experiment / "run_summary.csv")
        decisions = pd.read_csv(experiment / "final_population_decision_vectors.csv")
        objective_constraints = pd.read_csv(
            experiment / "final_population_objectives_constraints.csv"
        )
        protocol = yaml.safe_load((experiment / "config_snapshot.yaml").read_text(encoding="utf-8"))
        expected_runs = len(protocol["algorithms"]) * len(protocol["seeds"])
        require(len(runs) == expected_runs, "Run summary covers every algorithm-seed pair", checks)
        require(
            generations.groupby(["algorithm", "run_id"])["generation"].nunique().eq(protocol["generations"]).all(),
            "Every run has a complete generation trace",
            checks,
        )
        decision_columns = [column for column in decisions if column.startswith("x_r")]
        require(len(decision_columns) == 248, "Decision-vector output has 248 variables", checks)
        constraint_columns = [column for column in objective_constraints if column.startswith("g_")]
        require(len(constraint_columns) == 7, "Final solutions expose seven constraints", checks)
        require(
            objective_constraints["data_status"].str.contains("surrogate").all(),
            "Final solutions disclose surrogate status",
            checks,
        )

    public = ROOT / "data" / "public"
    detailed = pd.read_csv(public / "moa_2024_detailed_fishery_statistics.csv")
    environment = pd.read_csv(public / "moa_fishery_environment_2024.csv")
    latest = pd.read_csv(public / "official_latest_aquatic_products_2025.csv")
    require(len(detailed) == 99, "MOA 2024 detailed extract has 99 records", checks)
    require(len(environment) == 12, "Fishery-environment extract has 12 records", checks)
    require(len(latest) == 6, "Latest national/Zhejiang extract has 6 records", checks)
    for name, frame in [
        ("MOA 2024 detailed", detailed),
        ("Fishery environment", environment),
        ("Latest national/Zhejiang", latest),
    ]:
        require(
            frame["data_label"].eq("经过处理的数据（公开来源）").all(),
            f"{name} records disclose processed public-source status",
            checks,
        )
        require(
            frame["source_sha256"].str.fullmatch(r"[0-9a-f]{64}").all(),
            f"{name} records retain official HTML SHA-256",
            checks,
        )
        normalized = frame["reported_value"] * frame["normalization_multiplier"]
        require(
            (frame["value"] - normalized).abs().le(1e-6).all(),
            f"{name} normalized values reconcile to reported values",
            checks,
        )

    target = ROOT / "results" / "PACKAGE_VALIDATION.csv"
    pd.DataFrame(checks).to_csv(target, index=False)
    print(f"{len(checks)} reproducibility checks passed")
    print(target.resolve())


if __name__ == "__main__":
    main()
