from __future__ import annotations

import numpy as np
from pymoo.core.problem import Problem
from pymoo.core.repair import Repair
from pymoo.core.sampling import Sampling


N_REGIONS = 31
N_SECTORS = 4
N_MODES = 2
N_VARIABLES = N_REGIONS * N_SECTORS * N_MODES
CAPTURE_SECTORS = (0, 1)
AQUACULTURE_SECTORS = (2, 3)
PROCESSING_MODE = 1
OBJECTIVE_NAMES = ("social_reliability", "economic_efficiency", "ecological_security")
CONSTRAINT_NAMES = (
    "national_capture_tac",
    "capture_share",
    "national_processing_capacity",
    "national_total_supply",
    "regional_cold_storage",
    "minimum_supply",
    "fleet_power",
)


class FisheryPPMSProblem(Problem):
    """A public-data surrogate for the article's unreleased 248-variable model.

    The structure follows Equations 1-7. Coefficients that the article does not
    publish are deterministic proxies and must be replaced for strict author-level
    reproduction.
    """

    def __init__(self, seed: int = 1809036):
        super().__init__(n_var=N_VARIABLES, n_obj=3, n_ieq_constr=7, xl=0.0, xu=1.0)
        rng = np.random.default_rng(seed)
        raw_region = np.linspace(1.5, 0.45, N_REGIONS) * rng.uniform(0.82, 1.18, N_REGIONS)
        self.region_share = raw_region / raw_region.sum()

        sector_share = np.array([0.135, 0.049, 0.337, 0.479])
        mode_share = np.array([0.69, 0.31])
        baseline_total = 71_161_716.0
        self.ub_amount = (
            baseline_total
            * 1.20
            * self.region_share[:, None, None]
            * sector_share[None, :, None]
            * mode_share[None, None, :]
        )

        coastal = np.linspace(1.0, 0.15, N_REGIONS)
        self.digital_index = np.clip(0.35 + 0.55 * coastal + rng.normal(0, 0.04, N_REGIONS), 0.25, 0.95)
        self.workforce = 11_762_300 * self.region_share * rng.uniform(0.85, 1.15, N_REGIONS)
        self.cold_capacity = baseline_total * self.region_share * np.clip(0.12 + 0.33 * coastal, 0.12, 0.45)
        self.power_capacity = 18_940_154 * self.region_share * rng.uniform(0.92, 1.08, N_REGIONS)

        self.income_coeff = np.array(
            [[0.65, 0.82], [0.70, 0.86], [0.84, 1.02], [0.88, 1.06]], dtype=float
        )
        self.value_coeff = np.array(
            [[0.62, 0.95], [0.67, 0.99], [0.80, 1.16], [0.84, 1.20]], dtype=float
        )
        self.cost_coeff = np.array(
            [[0.29, 0.36], [0.26, 0.34], [0.33, 0.41], [0.31, 0.39]], dtype=float
        )
        self.eco_coeff = np.array(
            [[0.28, 0.31], [0.42, 0.45], [0.78, 0.81], [0.88, 0.91]], dtype=float
        )
        self.power_coeff = np.array([1.00, 0.70, 0.11, 0.08])

        self.catch_limit = 13_065_600.0
        self.total_limit = baseline_total * 1.10
        self.processing_limit = baseline_total * 0.37
        self.minimum_supply = baseline_total * 0.58
        self.power_limit = 18_940_154.0

        max_amount = self.ub_amount
        self.f1_scale = np.sum(max_amount * self.income_coeff[None, :, :] / self.workforce[:, None, None])
        net_value = self.value_coeff[None, :, :] * self.digital_index[:, None, None] - self.cost_coeff[None, :, :]
        self.f2_scale = max(np.sum(max_amount * np.maximum(net_value, 0)), 1.0)

    def decode(self, X: np.ndarray) -> np.ndarray:
        """Convert normalized decision variables to tonnes.

        Axis order is ``candidate, region, sector, mode``.  The 248 normalized
        variables are therefore an explicit 31 x 4 x 2 tensor, rather than an
        opaque vector whose indices cannot be audited.
        """
        values = np.atleast_2d(X).reshape(-1, N_REGIONS, N_SECTORS, N_MODES)
        return values * self.ub_amount[None, :, :, :]

    def evaluate_components(self, X: np.ndarray) -> dict[str, np.ndarray]:
        """Return every intermediate quantity used by the objective/constraint model.

        Keeping these arrays available is important for a research artifact:
        reviewers can independently recompute all three objectives and all seven
        constraint residuals.  A residual ``<= 0`` is feasible.
        """
        amount = self.decode(X)
        total = amount.sum(axis=(1, 2, 3))
        capture = amount[:, :, CAPTURE_SECTORS, :].sum(axis=(1, 2, 3))
        aquaculture = amount[:, :, AQUACULTURE_SECTORS, :].sum(axis=(1, 2, 3))
        processed_by_region = amount[:, :, :, PROCESSING_MODE].sum(axis=2)
        processed_total = processed_by_region.sum(axis=1)

        social = (amount * self.income_coeff[None, None, :, :] / self.workforce[None, :, None, None]).sum(axis=(1, 2, 3)) / self.f1_scale
        net_value = self.value_coeff[None, None, :, :] * self.digital_index[None, :, None, None] - self.cost_coeff[None, None, :, :]
        economic = (amount * net_value).sum(axis=(1, 2, 3)) / self.f2_scale
        eco_weighted = (amount * self.eco_coeff[None, None, :, :]).sum(axis=(1, 2, 3)) / np.maximum(total, 1.0)
        ecological = np.clip(0.72 * eco_weighted + 0.28 * (1 - capture / self.catch_limit), 0, 1)
        objectives = np.column_stack([social, economic, ecological])

        power_by_region = (amount.sum(axis=3) * self.power_coeff[None, None, :]).sum(axis=2)
        capture_ratio = capture / np.maximum(total, 1.0)
        constraints = np.column_stack(
            [
                capture / self.catch_limit - 1,
                capture_ratio - 0.28,
                processed_total / self.processing_limit - 1,
                total / self.total_limit - 1,
                np.max(processed_by_region / self.cold_capacity[None, :] - 1, axis=1),
                self.minimum_supply / np.maximum(total, 1.0) - 1,
                power_by_region.sum(axis=1) / self.power_limit - 1,
            ]
        )
        return {
            "amount": amount,
            "total": total,
            "capture": capture,
            "aquaculture": aquaculture,
            "processed_by_region": processed_by_region,
            "processed_total": processed_total,
            "power_by_region": power_by_region,
            "objectives": objectives,
            "constraints": constraints,
        }

    def _objectives_and_constraints(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        components = self.evaluate_components(X)
        return components["objectives"], components["constraints"]

    def _evaluate(self, X: np.ndarray, out: dict, *args, **kwargs) -> None:
        objectives, constraints = self._objectives_and_constraints(X)
        out["F"] = -objectives
        out["G"] = constraints

    def repair(self, X: np.ndarray) -> np.ndarray:
        """Apply deterministic constraint-feedback repair.

        Each iteration performs three traceable operations: scale capture to the
        national TAC, scale processing to each region's cold-storage capacity,
        then increase aquaculture variables when supply is below its minimum.
        Remaining constraints are retained as explicit selection pressure.
        """
        repaired = np.clip(np.atleast_2d(X).copy(), 0, 1).reshape(-1, N_REGIONS, N_SECTORS, N_MODES)
        for _ in range(3):
            amount = repaired * self.ub_amount[None, :, :, :]
            capture = amount[:, :, CAPTURE_SECTORS, :].sum(axis=(1, 2, 3))
            capture_scale = np.minimum(1.0, self.catch_limit / np.maximum(capture, 1.0))
            repaired[:, :, CAPTURE_SECTORS, :] *= capture_scale[:, None, None, None]

            amount = repaired * self.ub_amount[None, :, :, :]
            processed = amount[:, :, :, PROCESSING_MODE].sum(axis=2)
            regional_scale = np.minimum(1.0, self.cold_capacity[None, :] / np.maximum(processed, 1.0))
            repaired[:, :, :, PROCESSING_MODE] *= regional_scale[:, :, None]

            amount = repaired * self.ub_amount[None, :, :, :]
            total = amount.sum(axis=(1, 2, 3))
            low = total < self.minimum_supply
            if np.any(low):
                low_rows = repaired[low].copy()
                low_rows[:, :, AQUACULTURE_SECTORS, :] = np.minimum(
                    1.0, low_rows[:, :, AQUACULTURE_SECTORS, :] * 1.18 + 0.04
                )
                repaired[low] = low_rows
        return repaired.reshape(-1, N_VARIABLES)


class ChaoticSampling(Sampling):
    def __init__(self, seed: int = 1809036, mu: float = 4.0):
        super().__init__()
        self.seed = seed
        self.mu = mu

    def _do(self, problem: Problem, n_samples: int, **kwargs) -> np.ndarray:
        rng = np.random.default_rng(self.seed)
        z = float(rng.uniform(0.05, 0.95))
        values = np.empty(n_samples * problem.n_var)
        for index in range(values.size):
            z = self.mu * z * (1 - z)
            values[index] = z
        return values.reshape(n_samples, problem.n_var)


class ConstraintFeedbackRepair(Repair):
    def _do(self, problem: FisheryPPMSProblem, X: np.ndarray, **kwargs) -> np.ndarray:
        return problem.repair(X)
