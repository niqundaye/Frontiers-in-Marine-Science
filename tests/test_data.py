import numpy as np

from fishery_repro.calibrated import generate_calibrated_data
from fishery_repro.dataset import audit_tables, load_table


def test_paper_tables_have_expected_rows():
    assert len(load_table(1)) == 3
    assert len(load_table(2)) == 10
    assert len(load_table(3)) == 10
    assert len(load_table(4)) == 14


def test_reported_anchor_values_are_preserved():
    data = generate_calibrated_data()
    hv = data["figure_02_convergence"]
    final = hv[(hv.metric == "HV") & (hv.algorithm == "IA-NSGA-III")].sort_values("generation").iloc[-1]
    assert np.isclose(final.value, 0.960)
    box = data["figure_03_boxplots"]
    assert len(box) == 4 * 30 * 2


def test_data_audit_has_no_unexplained_large_2023_capacity_errors():
    audit = audit_tables()
    official = audit[audit.check.str.startswith("official_2023")]
    assert (official.status == "pass").all()

