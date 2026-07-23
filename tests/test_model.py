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

