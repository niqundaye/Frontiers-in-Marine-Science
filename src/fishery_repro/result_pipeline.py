from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

from . import figures
from .calibrated import ALGORITHMS


DATA_STATUS = "经过处理的数据 / processed data; not author-run logs"
INDICATORS = ("Social reliability", "Economic efficiency", "Ecological security")


@dataclass(frozen=True)
class ColumnRule:
    kind: str
    nullable: bool = False
    minimum: float | None = None
    maximum: float | None = None
    allowed: tuple[str, ...] | None = None


@dataclass(frozen=True)
class FigureSpec:
    number: int
    title: str
    input_file: str | None
    columns: dict[str, ColumnRule]
    unique_key: tuple[str, ...]
    transformations: tuple[str, ...]


def _num(
    minimum: float | None = None,
    maximum: float | None = None,
    *,
    nullable: bool = False,
) -> ColumnRule:
    return ColumnRule("number", nullable=nullable, minimum=minimum, maximum=maximum)


def _text(*allowed: str) -> ColumnRule:
    return ColumnRule("string", allowed=tuple(allowed) or None)


FIGURE_SPECS: dict[int, FigureSpec] = {
    1: FigureSpec(
        1,
        "PPMS-MOO and IA-NSGA-III architecture",
        None,
        {},
        (),
        (
            "Declare the 31 x 4 x 2 decision tensor.",
            "Map three objectives and seven inequality constraints.",
            "Connect chaotic sampling, constraint repair and adaptive reference relocation.",
        ),
    ),
    2: FigureSpec(
        2,
        "Convergence comparison",
        "input_data.csv",
        {
            "generation": _num(0, 1000),
            "algorithm": _text(*ALGORITHMS),
            "value": _num(0, 1),
            "metric": _text("HV", "IGD"),
        },
        ("generation", "algorithm", "metric"),
        (
            "Sort each algorithm-metric trajectory by generation.",
            "Integrate each curve by the trapezoidal rule.",
            "Report initial, terminal and absolute change values.",
        ),
    ),
    3: FigureSpec(
        3,
        "Thirty-run statistical comparison",
        "input_data.csv",
        {
            "run": _num(1, 30),
            "algorithm": _text(*ALGORITHMS),
            "metric": _text("HV", "IGD"),
            "value": _num(0, 1),
        },
        ("run", "algorithm", "metric"),
        (
            "Verify exactly 30 independent run identifiers per algorithm-metric cell.",
            "Compute mean, sample SD, median, quartiles, minimum and maximum.",
        ),
    ),
    4: FigureSpec(
        4,
        "Three-objective KPI radar",
        "input_data.csv",
        {
            "algorithm": _text(*ALGORITHMS),
            "indicator": _text(*INDICATORS),
            "value": _num(0, 1),
        },
        ("algorithm", "indicator"),
        (
            "Verify one value per algorithm-indicator cell.",
            "Compute mean, minimum and maximum objective score per algorithm.",
        ),
    ),
    5: FigureSpec(
        5,
        "Pareto-set comparison",
        "input_data.csv",
        {
            "algorithm": _text("IA-NSGA-III", "NSGA-III"),
            "F1": _num(0, 1),
            "F2": _num(0, 1),
            "F3": _num(0, 1),
        },
        (),
        (
            "Convert maximization objectives to minimization costs (1-F).",
            "Identify non-dominated points within each algorithm.",
            "Compute Euclidean distance to the ideal point (1,1,1).",
        ),
    ),
    6: FigureSpec(
        6,
        "Parameter sensitivity",
        "input_data.csv",
        {
            "parameter": _text("adaptive_factor", "relocation_frequency"),
            "setting": _num(0),
            "hv": _num(0, 1),
            "sd": _num(0, 1),
        },
        ("parameter", "setting"),
        (
            "Compute lower and upper one-SD bands.",
            "Rank settings by HV within each parameter and identify the optimum.",
        ),
    ),
    7: FigureSpec(
        7,
        "Digitalization sensitivity",
        "input_data.csv",
        {
            "alpha": _num(1.0, 1.5),
            "indicator": _text(*INDICATORS),
            "algorithm": _text(*ALGORITHMS),
            "value": _num(0, 1),
        },
        ("alpha", "indicator", "algorithm"),
        (
            "Fit a first-order sensitivity slope for each algorithm-indicator pair.",
            "Report endpoint change across alpha=1.0 to 1.5.",
        ),
    ),
    8: FigureSpec(
        8,
        "TAC policy sensitivity",
        "input_data.csv",
        {
            "record_type": _text("pareto", "hv"),
            "tac": _num(0.9, 1.1),
            "social": _num(0, 1, nullable=True),
            "economic": _num(0, 1, nullable=True),
            "ecological": _num(0, 1, nullable=True),
            "hv": _num(0, 1, nullable=True),
            "sd": _num(0, 1, nullable=True),
        },
        (),
        (
            "Validate conditional fields for Pareto and HV record types.",
            "Summarize objective centroids and HV uncertainty for every TAC scenario.",
        ),
    ),
    9: FigureSpec(
        9,
        "Algorithm-component ablation",
        "input_data.csv",
        {
            "generation": _num(0, 1000),
            "indicator": _text(*INDICATORS),
            "variant": _text(
                "IA-NSGA-III",
                "I-NSGA-III",
                "A-NSGA-III",
                "NSGA-III",
                "NSGA-II",
            ),
            "value": _num(0, 1.05),
        },
        ("generation", "indicator", "variant"),
        (
            "Sort every ablation trajectory by generation.",
            "Report terminal value and generation reaching 95% of its terminal value.",
        ),
    ),
    10: FigureSpec(
        10,
        "PPM-module ablation",
        "input_data.csv",
        {
            "scenario": _text("Proposed", "No-Marketing", "No-Processing", "Traditional"),
            "indicator": _text(*INDICATORS),
            "value": _num(0, 1),
            "sd": _num(0, 1),
        },
        ("scenario", "indicator"),
        (
            "Compute one-SD uncertainty bounds.",
            "Compute absolute and relative loss against the Proposed scenario.",
        ),
    ),
}


def _validate_schema(frame: pd.DataFrame, spec: FigureSpec) -> list[str]:
    checks: list[str] = []
    missing = set(spec.columns).difference(frame.columns)
    if missing:
        raise ValueError(f"Figure {spec.number}: missing columns {sorted(missing)}")
    for column, rule in spec.columns.items():
        series = frame[column]
        if not rule.nullable and series.isna().any():
            raise ValueError(f"Figure {spec.number}: {column} contains null values")
        present = series.dropna()
        if rule.kind == "number":
            converted = pd.to_numeric(present, errors="coerce")
            if converted.isna().any() or not np.isfinite(converted).all():
                raise ValueError(f"Figure {spec.number}: {column} is not finite numeric data")
            if rule.minimum is not None and (converted < rule.minimum - 1e-12).any():
                raise ValueError(f"Figure {spec.number}: {column} is below {rule.minimum}")
            if rule.maximum is not None and (converted > rule.maximum + 1e-12).any():
                raise ValueError(f"Figure {spec.number}: {column} is above {rule.maximum}")
        elif rule.allowed is not None:
            unexpected = set(present.astype(str)).difference(rule.allowed)
            if unexpected:
                raise ValueError(f"Figure {spec.number}: unexpected {column} values {sorted(unexpected)}")
        checks.append(f"{column}: {rule.kind}, valid")
    if spec.unique_key and frame.duplicated(list(spec.unique_key)).any():
        raise ValueError(f"Figure {spec.number}: duplicate key {spec.unique_key}")
    if spec.unique_key:
        checks.append(f"unique key {spec.unique_key}: valid")
    return checks


def _semantic_checks(number: int, frame: pd.DataFrame) -> list[str]:
    checks: list[str] = []
    if number == 2:
        sizes = frame.groupby(["algorithm", "metric"])["generation"].nunique()
        if sizes.nunique() != 1:
            raise ValueError("Figure 2 trajectories do not share a common generation grid")
        checks.append(f"common generation grid: {int(sizes.iloc[0])} points")
    elif number == 3:
        counts = frame.groupby(["algorithm", "metric"])["run"].nunique()
        if not (counts == 30).all():
            raise ValueError(f"Figure 3 must contain 30 runs per cell; observed {counts.to_dict()}")
        checks.append("30 run identifiers per algorithm-metric cell")
    elif number == 4:
        counts = frame.groupby("algorithm")["indicator"].nunique()
        if not (counts == 3).all():
            raise ValueError("Figure 4 requires three indicators per algorithm")
        checks.append("three indicators per algorithm")
    elif number == 8:
        pareto = frame["record_type"].eq("pareto")
        hv = frame["record_type"].eq("hv")
        if frame.loc[pareto, ["social", "economic", "ecological"]].isna().any().any():
            raise ValueError("Figure 8 Pareto rows require all three objectives")
        if frame.loc[hv, ["hv", "sd"]].isna().any().any():
            raise ValueError("Figure 8 HV rows require hv and sd")
        checks.append("conditional Pareto/HV fields valid")
    elif number == 10:
        counts = frame.groupby("indicator")["scenario"].nunique()
        if not (counts == 4).all():
            raise ValueError("Figure 10 requires four scenarios per indicator")
        checks.append("four scenarios per indicator")
    return checks


def _derive_figure_1(_: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"stage": 1, "component": "decision tensor", "implementation": "model.py::decode", "detail": "31 regions x 4 sectors x 2 modes = 248"},
            {"stage": 2, "component": "three objectives", "implementation": "model.py::evaluate_components", "detail": ", ".join(("social", "economic", "ecological"))},
            {"stage": 3, "component": "seven constraints", "implementation": "model.py::evaluate_components", "detail": "all residuals feasible when <= 0"},
            {"stage": 4, "component": "chaotic initialization", "implementation": "model.py::ChaoticSampling", "detail": "logistic map z(t+1)=mu*z(t)*(1-z(t))"},
            {"stage": 5, "component": "feedback repair", "implementation": "model.py::repair", "detail": "TAC, cold storage, minimum supply"},
            {"stage": 6, "component": "adaptive directions", "implementation": "experiment.py::GenerationAuditCallback", "detail": "nearest feasible objective ray relocation"},
        ]
    )


def _derive_figure_2(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (algorithm, metric), group in frame.groupby(["algorithm", "metric"], sort=True):
        ordered = group.sort_values("generation")
        rows.append(
            {
                "algorithm": algorithm,
                "metric": metric,
                "n_points": len(ordered),
                "initial_value": ordered["value"].iloc[0],
                "terminal_value": ordered["value"].iloc[-1],
                "absolute_change": ordered["value"].iloc[-1] - ordered["value"].iloc[0],
                "area_under_curve": np.trapezoid(ordered["value"], ordered["generation"]),
            }
        )
    return pd.DataFrame(rows)


def _derive_figure_3(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(["algorithm", "metric"], as_index=False)["value"]
        .agg(["count", "mean", "std", "median", "min", "max", lambda value: value.quantile(0.25), lambda value: value.quantile(0.75)])
        .reset_index()
        .rename(columns={"<lambda_0>": "q1", "<lambda_1>": "q3"})
    )


def _derive_figure_4(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("algorithm", as_index=False)["value"]
        .agg(["mean", "min", "max"])
        .reset_index()
    )


def _derive_figure_5(frame: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for algorithm, group in frame.groupby("algorithm", sort=True):
        result = group.copy()
        objectives = result[["F1", "F2", "F3"]].to_numpy(float)
        nd_ids = NonDominatedSorting().do(1 - objectives, only_non_dominated_front=True)
        result["non_dominated"] = False
        result.iloc[nd_ids, result.columns.get_loc("non_dominated")] = True
        result["distance_to_ideal"] = np.linalg.norm(1 - objectives, axis=1)
        result.insert(1, "point_id", np.arange(1, len(result) + 1))
        parts.append(result)
    return pd.concat(parts, ignore_index=True)


def _derive_figure_6(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["lower_1sd"] = result["hv"] - result["sd"]
    result["upper_1sd"] = result["hv"] + result["sd"]
    result["signal_to_noise"] = result["hv"] / result["sd"].replace(0, np.nan)
    result["rank_within_parameter"] = result.groupby("parameter")["hv"].rank(
        method="dense", ascending=False
    )
    result["is_best"] = result["rank_within_parameter"].eq(1)
    return result


def _derive_figure_7(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (algorithm, indicator), group in frame.groupby(["algorithm", "indicator"], sort=True):
        ordered = group.sort_values("alpha")
        slope, intercept = np.polyfit(ordered["alpha"], ordered["value"], 1)
        rows.append(
            {
                "algorithm": algorithm,
                "indicator": indicator,
                "n_points": len(ordered),
                "linear_slope_per_alpha": slope,
                "linear_intercept": intercept,
                "endpoint_change": ordered["value"].iloc[-1] - ordered["value"].iloc[0],
            }
        )
    return pd.DataFrame(rows)


def _derive_figure_8(frame: pd.DataFrame) -> pd.DataFrame:
    pareto = (
        frame[frame["record_type"].eq("pareto")]
        .groupby("tac", as_index=False)
        .agg(
            pareto_points=("record_type", "size"),
            social_mean=("social", "mean"),
            economic_mean=("economic", "mean"),
            ecological_mean=("ecological", "mean"),
        )
    )
    hv = frame[frame["record_type"].eq("hv")][["tac", "hv", "sd"]]
    return pareto.merge(hv, on="tac", how="outer").sort_values("tac")


def _derive_figure_9(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (indicator, variant), group in frame.groupby(["indicator", "variant"], sort=True):
        ordered = group.sort_values("generation")
        terminal = float(ordered["value"].iloc[-1])
        threshold = 0.95 * terminal
        reaching = ordered.loc[ordered["value"] >= threshold, "generation"]
        rows.append(
            {
                "indicator": indicator,
                "variant": variant,
                "terminal_value": terminal,
                "generation_at_95pct_terminal": int(reaching.iloc[0]) if len(reaching) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _derive_figure_10(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["lower_1sd"] = result["value"] - result["sd"]
    result["upper_1sd"] = result["value"] + result["sd"]
    baseline = result[result["scenario"].eq("Proposed")].set_index("indicator")["value"]
    result["proposed_value"] = result["indicator"].map(baseline)
    result["absolute_loss_vs_proposed"] = result["proposed_value"] - result["value"]
    result["relative_loss_vs_proposed"] = (
        result["absolute_loss_vs_proposed"] / result["proposed_value"]
    )
    return result


DERIVERS: dict[int, Callable[[pd.DataFrame], pd.DataFrame]] = {
    1: _derive_figure_1,
    2: _derive_figure_2,
    3: _derive_figure_3,
    4: _derive_figure_4,
    5: _derive_figure_5,
    6: _derive_figure_6,
    7: _derive_figure_7,
    8: _derive_figure_8,
    9: _derive_figure_9,
    10: _derive_figure_10,
}


def run_figure_pipeline(
    figure_number: int,
    bundle_dir: str | Path,
    *,
    formats: tuple[str, ...] = ("png", "svg"),
    dpi: int = 220,
) -> dict[str, Any]:
    """Validate, derive and render one self-contained result bundle."""
    if figure_number not in FIGURE_SPECS:
        raise ValueError(f"Unknown figure number: {figure_number}")
    spec = FIGURE_SPECS[figure_number]
    bundle = Path(bundle_dir)
    bundle.mkdir(parents=True, exist_ok=True)
    input_path = bundle / spec.input_file if spec.input_file else None
    frame = pd.read_csv(input_path) if input_path else pd.DataFrame()
    schema_checks = _validate_schema(frame, spec)
    semantic_checks = _semantic_checks(figure_number, frame)
    derived = DERIVERS[figure_number](frame)
    derived.insert(0, "data_status", DATA_STATUS)
    derived_path = bundle / "derived_data.csv"
    derived.to_csv(derived_path, index=False)

    report = {
        "schema_version": "1.0",
        "figure": figure_number,
        "title": spec.title,
        "data_status": DATA_STATUS,
        "input": None if input_path is None else input_path.name,
        "input_sha256": None if input_path is None else hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "input_rows": len(frame),
        "input_columns": list(frame.columns),
        "schema_checks": schema_checks,
        "semantic_checks": semantic_checks,
        "transformations": list(spec.transformations),
        "derived_rows": len(derived),
        "status": "pass",
    }
    report_path = bundle / "validation_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    output_dir = bundle / "generated_from_processed_data"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures._style()
    plotter = getattr(figures, f"figure_{figure_number:02d}")
    if input_path is None:
        plot_paths = plotter(output_dir, formats, dpi)
    else:
        plot_paths = plotter(frame, output_dir, formats, dpi)
    return {
        "derived_data": derived_path,
        "validation_report": report_path,
        "plots": plot_paths,
    }
