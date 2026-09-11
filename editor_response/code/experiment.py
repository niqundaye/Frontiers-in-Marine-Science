from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from pymoo.core.callback import Callback
from pymoo.core.problem import Problem
from pymoo.indicators.hv import HV
from pymoo.indicators.igd import IGD
from pymoo.optimize import minimize
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

from .benchmark import build_algorithm
from .model import (
    CONSTRAINT_NAMES,
    N_MODES,
    N_REGIONS,
    N_SECTORS,
    N_VARIABLES,
    OBJECTIVE_NAMES,
    FisheryPPMSProblem,
)


DATA_STATUS = "经过处理的数据 / public-data surrogate; not author-run logs"


@dataclass(frozen=True)
class OperatorConfig:
    crossover_probability: float = 1.0
    crossover_eta: float = 20.0
    mutation_probability: float = 1 / N_VARIABLES
    mutation_eta: float = 20.0
    chaotic_mu: float = 4.0
    relocation_frequency: int = 50
    adaptive_factor: float = 0.1
    constraint_penalty: float = 100.0


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    algorithms: tuple[str, ...]
    seeds: tuple[int, ...]
    population: int
    generations: int
    problem_seed: int
    operator: OperatorConfig
    save_decision_vectors: bool = True
    data_status: str = DATA_STATUS


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    """Load and strictly validate an experiment protocol from YAML."""
    source = Path(path)
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    required = {"name", "algorithms", "seeds", "population", "generations", "problem_seed"}
    missing = required.difference(raw)
    if missing:
        raise ValueError(f"Missing experiment keys: {sorted(missing)}")
    algorithms = tuple(str(value) for value in raw["algorithms"])
    seeds = tuple(int(value) for value in raw["seeds"])
    if not algorithms or not seeds:
        raise ValueError("algorithms and seeds must be non-empty")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be unique")
    population = int(raw["population"])
    generations = int(raw["generations"])
    if population < 8 or generations < 2:
        raise ValueError("population must be >= 8 and generations must be >= 2")
    operator_raw = raw.get("operator", {})
    operator = OperatorConfig(
        **{key: operator_raw[key] for key in asdict(OperatorConfig()) if key in operator_raw}
    )
    if not 0 < operator.crossover_probability <= 1:
        raise ValueError("crossover_probability must be in (0, 1]")
    if not 0 < operator.mutation_probability <= 1:
        raise ValueError("mutation_probability must be in (0, 1]")
    if operator.relocation_frequency < 1:
        raise ValueError("relocation_frequency must be >= 1")
    if not 0 <= operator.adaptive_factor <= 1:
        raise ValueError("adaptive_factor must be in [0, 1]")
    if operator.constraint_penalty <= 0:
        raise ValueError("constraint_penalty must be > 0")
    return ExperimentConfig(
        name=str(raw["name"]),
        algorithms=algorithms,
        seeds=seeds,
        population=population,
        generations=generations,
        problem_seed=int(raw["problem_seed"]),
        operator=operator,
        save_decision_vectors=bool(raw.get("save_decision_vectors", True)),
        data_status=str(raw.get("data_status", DATA_STATUS)),
    )


class GenerationAuditCallback(Callback):
    """Record the complete optimization state needed for convergence auditing."""

    def __init__(
        self,
        *,
        algorithm_name: str,
        run_id: int,
        seed: int,
        relocation_frequency: int,
        adaptive_factor: float,
        evaluation_problem: FisheryPPMSProblem,
    ):
        super().__init__()
        self.algorithm_name = algorithm_name
        self.run_id = run_id
        self.seed = seed
        self.relocation_frequency = relocation_frequency
        self.adaptive_factor = adaptive_factor
        self.evaluation_problem = evaluation_problem
        self.rows: list[dict[str, Any]] = []
        self.relocation_events: list[dict[str, Any]] = []

    def _relocate_reference_directions(self, algorithm: Any) -> None:
        """Move each reference direction toward its nearest feasible objective ray."""
        if self.algorithm_name != "IA-NSGA-III":
            return
        if algorithm.n_gen % self.relocation_frequency != 0:
            return
        values = np.asarray(algorithm.pop.get("F"), dtype=float)
        feasible = np.asarray(algorithm.pop.get("FEAS"), dtype=bool).ravel()
        active = values[feasible] if feasible.any() else values
        if active.size == 0:
            return
        scores = -active
        scores -= scores.min(axis=0)
        scores /= np.maximum(scores.max(axis=0), 1e-12)
        scores /= np.maximum(scores.sum(axis=1, keepdims=True), 1e-12)
        directions = np.asarray(algorithm.survival.ref_dirs, dtype=float)
        squared_distance = ((directions[:, None, :] - scores[None, :, :]) ** 2).sum(axis=2)
        targets = scores[np.argmin(squared_distance, axis=1)]
        relocated = (1 - self.adaptive_factor) * directions + self.adaptive_factor * targets
        relocated /= np.maximum(relocated.sum(axis=1, keepdims=True), 1e-12)
        mean_shift = float(np.linalg.norm(relocated - directions, axis=1).mean())
        algorithm.survival.ref_dirs = relocated
        if hasattr(algorithm, "ref_dirs"):
            algorithm.ref_dirs = relocated
        self.relocation_events.append(
            {
                "algorithm": self.algorithm_name,
                "run_id": self.run_id,
                "seed": self.seed,
                "generation": int(algorithm.n_gen),
                "mean_direction_shift": mean_shift,
            }
        )

    def notify(self, algorithm: Any) -> None:
        self._relocate_reference_directions(algorithm)
        x = np.asarray(algorithm.pop.get("X"), dtype=float)
        values, constraints = self.evaluation_problem._objectives_and_constraints(x)
        values = -values
        feasible = (constraints <= 0).all(axis=1)
        violation = np.maximum(constraints, 0).sum(axis=1)
        selected = values[feasible] if feasible.any() else values
        objectives = -selected
        nd_count = len(
            NonDominatedSorting().do(selected, only_non_dominated_front=True)
        )
        hv_zero = float(HV(ref_point=np.zeros(3))(selected))
        self.rows.append(
            {
                "algorithm": self.algorithm_name,
                "run_id": self.run_id,
                "seed": self.seed,
                "generation": int(algorithm.n_gen),
                "evaluations": int(algorithm.evaluator.n_eval),
                "population_size": int(len(values)),
                "feasible_count": int(feasible.sum()),
                "feasible_fraction": float(feasible.mean()),
                "mean_total_constraint_violation": float(violation.mean()),
                "max_total_constraint_violation": float(violation.max()),
                "non_dominated_count": int(nd_count),
                "hv_against_zero_reference": hv_zero,
                "max_social_reliability": float(objectives[:, 0].max()),
                "max_economic_efficiency": float(objectives[:, 1].max()),
                "max_ecological_security": float(objectives[:, 2].max()),
                "data_status": DATA_STATUS,
            }
        )


class ConstraintPenaltyProblem(Problem):
    """Unconstrained penalty view used only for pymoo's MOEA/D implementation.

    The original seven residuals remain available through ``base_problem`` and are
    re-evaluated for every logged population and final solution.
    """

    def __init__(self, base_problem: FisheryPPMSProblem, penalty: float):
        super().__init__(
            n_var=base_problem.n_var,
            n_obj=base_problem.n_obj,
            n_ieq_constr=0,
            xl=base_problem.xl,
            xu=base_problem.xu,
        )
        self.base_problem = base_problem
        self.penalty = penalty

    def _evaluate(self, x: np.ndarray, out: dict[str, np.ndarray], *args: Any, **kwargs: Any) -> None:
        objectives, constraints = self.base_problem._objectives_and_constraints(x)
        violation = np.maximum(constraints, 0).sum(axis=1)
        out["F"] = -objectives + self.penalty * violation[:, None]


def _decision_columns() -> list[str]:
    return [
        f"x_r{region + 1:02d}_s{sector + 1}_m{mode + 1}"
        for region in range(N_REGIONS)
        for sector in range(N_SECTORS)
        for mode in range(N_MODES)
    ]


def _final_population_rows(
    *,
    problem: FisheryPPMSProblem,
    algorithm_name: str,
    run_id: int,
    seed: int,
    population: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    x = np.asarray(population.get("X"), dtype=float)
    objectives, g = problem._objectives_and_constraints(x)
    f = -objectives
    feasible = (g <= 0).all(axis=1)
    components = problem.evaluate_components(x)
    solution_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    x_columns = _decision_columns()
    for index in range(len(x)):
        base: dict[str, Any] = {
            "algorithm": algorithm_name,
            "run_id": run_id,
            "seed": seed,
            "solution_id": index + 1,
            "feasible": bool(feasible[index]),
            "total_constraint_violation": float(np.maximum(g[index], 0).sum()),
            "total_supply_tonnes": float(components["total"][index]),
            "capture_tonnes": float(components["capture"][index]),
            "aquaculture_tonnes": float(components["aquaculture"][index]),
            "processed_tonnes": float(components["processed_total"][index]),
            "data_status": DATA_STATUS,
        }
        base.update(
            {name: float(value) for name, value in zip(OBJECTIVE_NAMES, -f[index], strict=True)}
        )
        base.update(
            {f"g_{name}": float(value) for name, value in zip(CONSTRAINT_NAMES, g[index], strict=True)}
        )
        solution_rows.append(base)
        decision = {
            "algorithm": algorithm_name,
            "run_id": run_id,
            "seed": seed,
            "solution_id": index + 1,
        }
        decision.update({name: float(value) for name, value in zip(x_columns, x[index], strict=True)})
        decision_rows.append(decision)
    return solution_rows, decision_rows


def _add_quality_indicators(summary: pd.DataFrame, solutions: pd.DataFrame) -> pd.DataFrame:
    feasible = solutions[solutions["feasible"]].copy()
    objective_columns = list(OBJECTIVE_NAMES)
    source = feasible if not feasible.empty else solutions
    pooled_cost = 1 - np.clip(source[objective_columns].to_numpy(float), 0, 1)
    reference_ids = NonDominatedSorting().do(pooled_cost, only_non_dominated_front=True)
    reference_front = pooled_cost[reference_ids]
    hv = HV(ref_point=np.full(3, 1.05))
    igd = IGD(reference_front)
    records: list[dict[str, Any]] = []
    for row in summary.to_dict("records"):
        selected = solutions[
            (solutions["algorithm"] == row["algorithm"])
            & (solutions["run_id"] == row["run_id"])
        ]
        feasible_selected = selected[selected["feasible"]]
        metric_source = feasible_selected if not feasible_selected.empty else selected
        costs = 1 - np.clip(metric_source[objective_columns].to_numpy(float), 0, 1)
        row["hypervolume"] = float(hv(costs))
        row["igd_to_pooled_reference"] = float(igd(costs))
        row["metric_population"] = "feasible" if not feasible_selected.empty else "all_no_feasible"
        records.append(row)
    return pd.DataFrame(records)


def _package_versions() -> dict[str, str]:
    packages = ("numpy", "pandas", "pymoo", "scipy", "PyYAML")
    return {name: importlib.metadata.version(name) for name in packages}


def run_experiment(
    config_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Run all configured independent repeats and write an auditable artifact."""
    config_source = Path(config_path)
    config = load_experiment_config(config_source)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    config_bytes = config_source.read_bytes()
    (target / "config_snapshot.yaml").write_bytes(config_bytes)

    generation_rows: list[dict[str, Any]] = []
    relocation_rows: list[dict[str, Any]] = []
    solution_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    run_rows: list[dict[str, Any]] = []
    started = datetime.now(timezone.utc)

    for algorithm_index, algorithm_name in enumerate(config.algorithms):
        for run_id, base_seed in enumerate(config.seeds, start=1):
            run_seed = int(base_seed + algorithm_index * 100_000)
            problem = FisheryPPMSProblem(seed=config.problem_seed)
            operator = asdict(config.operator)
            algorithm, _ = build_algorithm(
                algorithm_name,
                config.population,
                run_seed,
                **operator,
            )
            optimization_problem: Problem = problem
            if algorithm_name.lower().replace("_", "-") == "moea/d":
                optimization_problem = ConstraintPenaltyProblem(
                    problem,
                    penalty=config.operator.constraint_penalty,
                )
            callback = GenerationAuditCallback(
                algorithm_name=algorithm_name,
                run_id=run_id,
                seed=run_seed,
                relocation_frequency=config.operator.relocation_frequency,
                adaptive_factor=config.operator.adaptive_factor,
                evaluation_problem=problem,
            )
            tick = time.perf_counter()
            result = minimize(
                optimization_problem,
                algorithm,
                ("n_gen", config.generations),
                seed=run_seed,
                callback=callback,
                save_history=False,
                verbose=False,
            )
            elapsed = time.perf_counter() - tick
            rows, decisions = _final_population_rows(
                problem=problem,
                algorithm_name=algorithm_name,
                run_id=run_id,
                seed=run_seed,
                population=result.pop,
            )
            generation_rows.extend(callback.rows)
            relocation_rows.extend(callback.relocation_events)
            solution_rows.extend(rows)
            decision_rows.extend(decisions)
            final_log = callback.rows[-1]
            run_rows.append(
                {
                    "algorithm": algorithm_name,
                    "run_id": run_id,
                    "seed": run_seed,
                    "elapsed_seconds": elapsed,
                    "population": config.population,
                    "generations": config.generations,
                    "function_evaluations": final_log["evaluations"],
                    "feasible_fraction": final_log["feasible_fraction"],
                    "non_dominated_count": final_log["non_dominated_count"],
                    "data_status": config.data_status,
                }
            )

    generations = pd.DataFrame(generation_rows)
    relocations = pd.DataFrame(
        relocation_rows,
        columns=["algorithm", "run_id", "seed", "generation", "mean_direction_shift"],
    )
    solutions = pd.DataFrame(solution_rows)
    summary = _add_quality_indicators(pd.DataFrame(run_rows), solutions)
    algorithm_summary = (
        summary.groupby("algorithm", as_index=False)
        .agg(
            runs=("run_id", "count"),
            hypervolume_mean=("hypervolume", "mean"),
            hypervolume_sd=("hypervolume", "std"),
            igd_mean=("igd_to_pooled_reference", "mean"),
            igd_sd=("igd_to_pooled_reference", "std"),
            feasible_fraction_mean=("feasible_fraction", "mean"),
            elapsed_seconds_mean=("elapsed_seconds", "mean"),
        )
        .assign(data_status=config.data_status)
    )

    outputs = {
        "generation_log": target / "generation_log.csv",
        "relocation_log": target / "reference_relocation_log.csv",
        "final_solutions": target / "final_population_objectives_constraints.csv",
        "run_summary": target / "run_summary.csv",
        "algorithm_summary": target / "algorithm_summary.csv",
        "metadata": target / "run_metadata.json",
    }
    generations.to_csv(outputs["generation_log"], index=False)
    relocations.to_csv(outputs["relocation_log"], index=False)
    solutions.to_csv(outputs["final_solutions"], index=False)
    summary.to_csv(outputs["run_summary"], index=False)
    algorithm_summary.to_csv(outputs["algorithm_summary"], index=False)
    if config.save_decision_vectors:
        outputs["decision_vectors"] = target / "final_population_decision_vectors.csv"
        pd.DataFrame(decision_rows).to_csv(outputs["decision_vectors"], index=False)

    completed = datetime.now(timezone.utc)
    metadata = {
        "schema_version": "1.0",
        "experiment": asdict(config),
        "data_status": config.data_status,
        "started_utc": started.isoformat(),
        "completed_utc": completed.isoformat(),
        "wall_clock_seconds": (completed - started).total_seconds(),
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": _package_versions(),
        },
        "model_dimensions": {
            "regions": N_REGIONS,
            "sectors": N_SECTORS,
            "modes": N_MODES,
            "decision_variables": N_VARIABLES,
            "objectives": list(OBJECTIVE_NAMES),
            "constraints": list(CONSTRAINT_NAMES),
        },
        "output_rows": {
            "generation_log": len(generations),
            "relocation_log": len(relocations),
            "final_solutions": len(solutions),
            "run_summary": len(summary),
        },
        "disclosure": (
            "This is an executable public-data surrogate. The article's province-level "
            "coefficient matrix and original 30-run logs were not available."
        ),
    }
    outputs["metadata"].write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return outputs
