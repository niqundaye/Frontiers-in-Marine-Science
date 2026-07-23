import json

from fishery_repro.calibrated import generate_calibrated_data
from fishery_repro.result_pipeline import run_figure_pipeline


def test_result_pipeline_writes_schema_audit_and_derived_data(tmp_path):
    bundle = tmp_path / "figure_03"
    bundle.mkdir()
    generate_calibrated_data()["figure_03_boxplots"].to_csv(
        bundle / "input_data.csv", index=False
    )
    outputs = run_figure_pipeline(3, bundle, formats=("png",), dpi=80)
    report = json.loads(outputs["validation_report"].read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["input_rows"] == 240
    assert outputs["derived_data"].is_file()
    assert len(outputs["plots"]) == 1
