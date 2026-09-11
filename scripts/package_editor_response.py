from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "editor_response"
ZIP_PATH = ROOT / "fishery_editor_response_package_2026-09-11.zip"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_environment_files() -> None:
    code = PACKAGE / "code"
    code.mkdir(parents=True, exist_ok=True)
    for name in ["requirements.txt", "requirements-dev.txt", "pyproject.toml", "environment.yml", "LICENSE"]:
        shutil.copy2(ROOT / name, code / name)


def validate() -> dict[str, object]:
    province = pd.read_csv(PACKAGE / "data" / "reconstructed" / "province_inputs.csv")
    matrix = pd.read_csv(PACKAGE / "data" / "reconstructed" / "coefficient_matrix_248_rows.csv")
    runs = pd.read_csv(PACKAGE / "runs" / "new_30run_surrogate" / "run_summary.csv")
    generations = pd.read_csv(PACKAGE / "runs" / "new_30run_surrogate" / "generation_log.csv")
    metrics = pd.read_csv(PACKAGE / "runs" / "new_30run_surrogate" / "metric_recomputation_check.csv")
    calibrated = pd.read_csv(PACKAGE / "runs" / "article_figure3_calibrated" / "figure_03_calibrated_30run_metrics.csv")
    checks = {
        "province_rows_equal_31": len(province) == 31,
        "coefficient_rows_equal_248": len(matrix) == 248,
        "region_share_sums_to_one": abs(province["region_share_proxy"].sum() - 1.0) < 1e-12,
        "all_matrix_rows_marked_non_original": matrix["data_status"].str.contains("not historical", regex=False).all(),
        "four_algorithms_present": runs["algorithm"].nunique() == 4,
        "thirty_runs_per_algorithm": runs.groupby("algorithm")["run_id"].nunique().eq(30).all(),
        "run_rows_equal_120": len(runs) == 120,
        "generation_rows_equal_3600": len(generations) == 3600,
        "hv_recalculation_matches": metrics["hv_abs_difference"].max() < 1e-12,
        "igd_recalculation_matches": metrics["igd_abs_difference"].max() < 1e-12,
        "calibrated_figure3_has_30_per_algorithm_metric": calibrated.groupby(["algorithm", "metric"])["run"].nunique().eq(30).all(),
        "workbook_present": (PACKAGE / "03_Reconstructed_31_Province_Inputs.xlsx").exists(),
        "response_docx_present": (PACKAGE / "01_Response_to_Editor_DRAFT.docx").exists(),
        "response_pdf_present": (PACKAGE / "01_Response_to_Editor_DRAFT.pdf").exists(),
    }
    checks = {name: bool(passed) for name, passed in checks.items()}
    result = {
        "prepared_on": "2026-09-11",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "counts": {
            "province_rows": len(province),
            "coefficient_rows": len(matrix),
            "algorithms": runs["algorithm"].nunique(),
            "new_run_rows": len(runs),
            "generation_rows": len(generations),
            "calibrated_metric_rows": len(calibrated),
        },
        "maximum_metric_recalculation_difference": {
            "hv": float(metrics["hv_abs_difference"].max()),
            "igd": float(metrics["igd_abs_difference"].max()),
        },
        "disclosure": "PASS verifies package consistency only; it does not convert reconstructed/new material into historical original data.",
    }
    (PACKAGE / "PACKAGE_VALIDATION.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if result["status"] != "PASS":
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"Package validation failed: {failed}")
    return result


def write_manifest() -> int:
    manifest = PACKAGE / "SHA256SUMS.csv"
    files = [path for path in PACKAGE.rglob("*") if path.is_file() and path != manifest]
    with manifest.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256", "manifest_note"])
        writer.writeheader()
        for path in sorted(files, key=lambda item: item.relative_to(PACKAGE).as_posix()):
            writer.writerow(
                {
                    "path": path.relative_to(PACKAGE).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": digest(path),
                    "manifest_note": "SHA256SUMS.csv intentionally excludes its own self-hash",
                }
            )
    return len(files)


def build_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(PACKAGE.rglob("*"), key=lambda item: item.relative_to(PACKAGE).as_posix()):
            if path.is_file():
                archive.write(path, (Path("editor_response") / path.relative_to(PACKAGE)).as_posix())


def verify_zip(expected_manifest_rows: int) -> dict[str, object]:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        bad = archive.testzip()
        names = archive.namelist()
        manifest_rows = archive.read("editor_response/SHA256SUMS.csv").decode("utf-8-sig").splitlines()
    result = {
        "zip": str(ZIP_PATH),
        "bytes": ZIP_PATH.stat().st_size,
        "sha256": digest(ZIP_PATH),
        "members": len(names),
        "crc_error": bad,
        "manifest_data_rows": len(manifest_rows) - 1,
        "expected_manifest_data_rows": expected_manifest_rows,
    }
    if bad is not None or result["manifest_data_rows"] != expected_manifest_rows:
        raise RuntimeError(f"ZIP verification failed: {result}")
    return result


def main() -> None:
    copy_environment_files()
    validation = validate()
    rows = write_manifest()
    build_zip()
    verification = verify_zip(rows)
    print(json.dumps({"validation": validation, "zip_verification": verification}, indent=2))


if __name__ == "__main__":
    main()
