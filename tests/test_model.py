import numpy as np

from fishery_repro.model import FisheryPPMSProblem, N_VARIABLES


def test_problem_dimensions_and_finite_evaluation():
    problem = FisheryPPMSProblem()
    x = np.full((3, N_VARIABLES), 0.6)
    out = {}
    problem._evaluate(x, out)
    assert out["F"].shape == (3, 3)
    assert out["G"].shape == (3, 7)
    assert np.isfinite(out["F"]).all()
    assert np.isfinite(out["G"]).all()


def test_constraint_feedback_repair_stays_in_bounds():
    problem = FisheryPPMSProblem()
    repaired = problem.repair(np.full((2, N_VARIABLES), 1.2))
    assert repaired.min() >= 0
    assert repaired.max() <= 1


def test_problem_is_anchored_to_official_public_panel_and_paper_total():
    problem = FisheryPPMSProblem()
    assert len(problem.public_panel) == 31
    assert abs(problem.region_share.sum() - 1.0) < 1e-12
    assert abs(problem.calibrated_sector_tonnes.sum() - 71_161_716.0) < 1e-6
    assert problem.observed_2024_sector_tonnes.shape == (31, 4)
    assert problem.mode_share_by_sector.shape == (4, 2)
    assert np.allclose(problem.mode_share_by_sector.sum(axis=1), 1.0)
