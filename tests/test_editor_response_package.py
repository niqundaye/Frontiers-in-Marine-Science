from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "editor_response"


def test_reconstructed_matrix_dimensions_and_labels():
    provinces = pd.read_csv(PACKAGE / "data" / "reconstructed" / "province_inputs.csv")
    matrix = pd.read_csv(
        PACKAGE / "data" / "reconstructed" / "coefficient_matrix_248_rows.csv"
    )
    coefficients = pd.read_csv(
        PACKAGE / "data" / "reconstructed" / "sector_mode_coefficients.csv"
    )

    assert len(provinces) == 31
    assert len(matrix) == 248
    assert len(coefficients) == 8
    assert matrix["variable_id"].is_unique
    assert set(matrix["data_status"]) == {
        "calibrated reconstruction; not historical author input"
    }


def test_new_surrogate_run_counts_and_metric_recomputation():
    run_dir = PACKAGE / "runs" / "new_30run_surrogate"
    summary = pd.read_csv(run_dir / "run_summary.csv")
    checks = pd.read_csv(run_dir / "metric_recomputation_check.csv")

    assert set(summary["algorithm"]) == {
        "IA-NSGA-III",
        "NSGA-III",
        "MOEA/D",
        "NSGA-II",
    }
    assert summary.groupby("algorithm")["run_id"].nunique().eq(30).all()
    assert len(summary) == 120
    assert checks["hv_abs_difference"].max() < 1e-12
    assert checks["igd_abs_difference"].max() < 1e-12


def test_unavailable_materials_are_never_claimed_as_original():
    availability = pd.read_csv(PACKAGE / "02_Material_Availability.csv")
    unavailable = availability[
        availability["status"] == "unavailable_in_retained_archive"
    ]

    assert not unavailable.empty
    assert unavailable["may_be_described_as_original"].str.lower().eq("no").all()
