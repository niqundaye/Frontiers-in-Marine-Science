from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from pymoo.algorithms.moo.moead import MOEAD
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.core.callback import Callback
from pymoo.indicators.hv import HV
from pymoo.optimize import minimize
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.util.ref_dirs import get_reference_directions

from .config import ROOT
from .model import ChaoticSampling, ConstraintFeedbackRepair, FisheryPPMSProblem


class AdaptiveReferenceRelocation(Callback):
    def __init__(self, frequency: int = 50, gamma: float = 0.1):
        super().__init__()
        self.frequency = frequency
        self.gamma = gamma

    def notify(self, algorithm) -> None:
        if algorithm.n_gen == 0 or algorithm.n_gen % self.frequency != 0:
            return
        values = algorithm.pop.get("F")
        feasible = algorithm.pop.get("FEAS").ravel()
        values = values[feasible] if feasible.any() else values
        if values.size == 0:
            return
        scores = -values
        scores -= scores.min(axis=0)
        scores /= np.maximum(scores.max(axis=0), 1e-12)
        scores /= np.maximum(scores.sum(axis=1, keepdims=True), 1e-12)
        directions = np.asarray(algorithm.survival.ref_dirs)
        distance = ((directions[:, None, :] - scores[None, :, :]) ** 2).sum(axis=2)
        targets = scores[np.argmin(distance, axis=1)]
        relocated = (1 - self.gamma) * directions + self.gamma * targets
        relocated /= np.maximum(relocated.sum(axis=1, keepdims=True), 1e-12)
        algorithm.survival.ref_dirs = relocated
        if hasattr(algorithm, "ref_dirs"):
            algorithm.ref_dirs = relocated


def _reference_directions(population: int, seed: int) -> np.ndarray:
    return get_reference_directions("energy", 3, population, seed=seed)


def build_algorithm(name: str, population: int, seed: int):
    ref_dirs = _reference_directions(population, seed)
    crossover = SBX(prob=1.0, eta=20)
    mutation = PM(prob=1 / 248, eta=20)
    repair = ConstraintFeedbackRepair()
    normalized = name.lower().replace("_", "-")
    if normalized == "ia-nsga-iii":
        algorithm = NSGA3(
            pop_size=population,
            ref_dirs=ref_dirs,
            sampling=ChaoticSampling(seed=seed),
            crossover=crossover,
            mutation=mutation,
            repair=repair,
        )
        return algorithm, AdaptiveReferenceRelocation(frequency=5, gamma=0.1)
    if normalized == "nsga-iii":
        return NSGA3(pop_size=population, ref_dirs=ref_dirs, crossover=crossover, mutation=mutation), None
    if normalized == "nsga-ii":
        return NSGA2(pop_size=population, crossover=crossover, mutation=mutation), None
    if normalized == "moea/d":
        return MOEAD(ref_dirs=ref_dirs, n_neighbors=min(15, population - 1), prob_neighbor_mating=0.7, crossover=crossover, mutation=mutation), None
    raise ValueError(f"Unknown algorithm: {name}")


def run_smoke_benchmark(
    output: str | Path | None = None,
    population: int = 48,
    generations: int = 20,
    seed: int = 1809036,
) -> Path:
    target = Path(output) if output else ROOT / "results" / "benchmark" / "smoke_summary.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    problem = FisheryPPMSProblem(seed=seed)
    rows: list[dict[str, object]] = []
    for index, name in enumerate(["IA-NSGA-III", "NSGA-III", "NSGA-II"]):
        algorithm, callback = build_algorithm(name, population, seed + index)
        minimize_kwargs = {"seed": seed + index, "verbose": False}
        if callback is not None:
            minimize_kwargs["callback"] = callback
        result = minimize(problem, algorithm, ("n_gen", generations), **minimize_kwargs)
        population_f = result.pop.get("F")
        feasible = result.pop.get("FEAS").ravel()
        selected = population_f[feasible] if feasible.any() else population_f
        objectives = -selected
        hv = HV(ref_point=np.array([0.0, 0.0, 0.0]))(selected)
        rows.append(
            {
                "algorithm": name,
                "population": population,
                "generations": generations,
                "feasible_fraction": float(feasible.mean()),
                "hypervolume_surrogate": float(hv),
                "max_social": float(objectives[:, 0].max()),
                "max_economic": float(objectives[:, 1].max()),
                "max_ecological": float(objectives[:, 2].max()),
                "status": "public-data surrogate; not author-run replication",
            }
        )
    pd.DataFrame(rows).to_csv(target, index=False)
    return target
