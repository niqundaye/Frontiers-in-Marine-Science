from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import ROOT


ALGORITHMS = ["IA-NSGA-III", "NSGA-III", "MOEA/D", "NSGA-II"]


def _approach(g: np.ndarray, start: float, target: float, tau: float) -> np.ndarray:
    base = target - (target - start) * np.exp(-g / tau)
    correction = (target - base[-1]) * (g / g[-1])
    return base + correction


def _decline(g: np.ndarray, start: float, target: float, tau: float) -> np.ndarray:
    base = target + (start - target) * np.exp(-g / tau)
    correction = (target - base[-1]) * (g / g[-1])
    return np.maximum(base + correction, target)


def _long_frame(x: np.ndarray, values: dict[str, np.ndarray], x_name: str) -> pd.DataFrame:
    return pd.concat(
        [pd.DataFrame({x_name: x, "algorithm": key, "value": value}) for key, value in values.items()],
        ignore_index=True,
    )


def generate_calibrated_data(seed: int = 1809036, step: int = 10) -> dict[str, pd.DataFrame]:
    """Create traceable plot data anchored to values reported in the article.

    These are calibrated reconstructions, not recovered author run logs. Every file
    written by this function carries that status in the repository documentation.
    """
    rng = np.random.default_rng(seed)
    g = np.arange(0, 1001, step)

    hv_targets = dict(zip(ALGORITHMS, [0.960, 0.835, 0.730, 0.645], strict=True))
    hv_tau = dict(zip(ALGORITHMS, [135, 210, 300, 390], strict=True))
    hv = {
        name: _approach(g, 0.10 - idx * 0.01, hv_targets[name], hv_tau[name])
        for idx, name in enumerate(ALGORITHMS)
    }
    hv["IA-NSGA-III"] += 0.0015 * np.floor(g / 100) / 10
    hv["IA-NSGA-III"][-1] = 0.960

    igd_targets = dict(zip(ALGORITHMS, [0.012, 0.045, 0.085, 0.125], strict=True))
    igd_tau = dict(zip(ALGORITHMS, [105, 190, 260, 350], strict=True))
    igd = {
        name: _decline(g, 0.52 + idx * 0.07, igd_targets[name], igd_tau[name])
        for idx, name in enumerate(ALGORITHMS)
    }
    figure_02 = pd.concat(
        [
            _long_frame(g, hv, "generation").assign(metric="HV"),
            _long_frame(g, igd, "generation").assign(metric="IGD"),
        ],
        ignore_index=True,
    )

    run_specs = {
        "IA-NSGA-III": (0.958, 0.006, 0.012, 0.002),
        "NSGA-III": (0.835, 0.016, 0.045, 0.007),
        "MOEA/D": (0.748, 0.020, 0.085, 0.014),
        "NSGA-II": (0.670, 0.028, 0.128, 0.022),
    }
    box_rows: list[dict[str, object]] = []
    for algorithm, (hv_mean, hv_sd, igd_mean, igd_sd) in run_specs.items():
        for run, (hv_value, igd_value) in enumerate(
            zip(rng.normal(hv_mean, hv_sd, 30), rng.normal(igd_mean, igd_sd, 30), strict=True), 1
        ):
            box_rows.extend(
                [
                    {"run": run, "algorithm": algorithm, "metric": "HV", "value": hv_value},
                    {"run": run, "algorithm": algorithm, "metric": "IGD", "value": max(igd_value, 0)},
                ]
            )
    figure_03 = pd.DataFrame(box_rows)

    radar = {
        "IA-NSGA-III": [0.950, 0.880, 0.999],
        "NSGA-III": [0.840, 0.790, 0.935],
        "MOEA/D": [0.780, 0.740, 0.895],
        "NSGA-II": [0.710, 0.660, 0.825],
    }
    figure_04 = pd.DataFrame(
        [
            {"algorithm": alg, "indicator": indicator, "value": value}
            for alg, values in radar.items()
            for indicator, value in zip(["Social reliability", "Economic efficiency", "Ecological security"], values, strict=True)
        ]
    )

    pareto_rows: list[dict[str, object]] = []
    for algorithm, n, shift in [("IA-NSGA-III", 120, 0.0), ("NSGA-III", 80, 0.13)]:
        f1 = rng.beta(2.2, 1.7, n)
        f2 = np.clip(0.42 + 0.52 * (1 - f1) + rng.normal(0, 0.07, n) - shift, 0, 1)
        f3 = np.clip(0.38 + 0.48 * f1 + rng.normal(0, 0.09, n) - shift * 0.8, 0, 1)
        for a, b, c in zip(f1, f2, f3, strict=True):
            pareto_rows.append({"algorithm": algorithm, "F1": a, "F2": b, "F3": c})
    figure_05 = pd.DataFrame(pareto_rows)

    figure_06 = pd.concat(
        [
            pd.DataFrame(
                {
                    "parameter": "adaptive_factor",
                    "setting": [0.00, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40],
                    "hv": [0.860, 0.915, 0.958, 0.945, 0.920, 0.890, 0.850],
                    "sd": [0.014, 0.010, 0.004, 0.006, 0.009, 0.014, 0.020],
                }
            ),
            pd.DataFrame(
                {
                    "parameter": "relocation_frequency",
                    "setting": [0, 20, 50, 75, 100, 150, 200],
                    "hv": [0.880, 0.935, 0.958, 0.945, 0.925, 0.890, 0.870],
                    "sd": [0.016, 0.010, 0.004, 0.007, 0.010, 0.015, 0.021],
                }
            ),
        ],
        ignore_index=True,
    )

    alpha = np.round(np.arange(1.0, 1.51, 0.1), 1)
    sensitivity: dict[str, dict[str, list[float]]] = {
        "Social reliability": {
            "IA-NSGA-III": [0.88, 0.90, 0.92, 0.94, 0.95, 0.96],
            "NSGA-III": [0.81, 0.825, 0.835, 0.84, 0.845, 0.85],
            "MOEA/D": [0.74, 0.755, 0.765, 0.77, 0.78, 0.78],
            "NSGA-II": [0.68, 0.69, 0.70, 0.71, 0.715, 0.72],
        },
        "Economic efficiency": {
            "IA-NSGA-III": [0.81, 0.86, 0.90, 0.94, 0.96, 0.975],
            "NSGA-III": [0.76, 0.78, 0.80, 0.815, 0.825, 0.835],
            "MOEA/D": [0.71, 0.725, 0.74, 0.75, 0.755, 0.765],
            "NSGA-II": [0.63, 0.645, 0.66, 0.668, 0.675, 0.68],
        },
        "Ecological security": {
            "IA-NSGA-III": [0.999, 0.999, 1.000, 1.000, 1.000, 1.000],
            "NSGA-III": [0.925, 0.927, 0.932, 0.936, 0.938, 0.940],
            "MOEA/D": [0.885, 0.887, 0.890, 0.893, 0.896, 0.898],
            "NSGA-II": [0.820, 0.822, 0.825, 0.828, 0.832, 0.833],
        },
    }
    figure_07 = pd.DataFrame(
        [
            {"alpha": a, "indicator": indicator, "algorithm": algorithm, "value": value}
            for indicator, algorithms in sensitivity.items()
            for algorithm, values in algorithms.items()
            for a, value in zip(alpha, values, strict=True)
        ]
    )

    tac_rows: list[dict[str, object]] = []
    for tac, shift in [(0.9, 0.11), (1.0, 0.04), (1.1, -0.03)]:
        u = rng.uniform(0.05, 0.95, 90)
        v = rng.uniform(0.05, 0.95, 90)
        social = np.clip(0.48 + 0.42 * u - shift, 0, 1)
        economic = np.clip(0.45 + 0.45 * v - shift, 0, 1)
        ecological = np.clip(0.98 - 0.26 * (u + v) / 2 + shift * 0.7, 0, 1)
        for a, b, c in zip(social, economic, ecological, strict=True):
            tac_rows.append({"record_type": "pareto", "tac": tac, "social": a, "economic": b, "ecological": c})
    for tac, hv_value, sd in [(0.9, 0.942, 0.005), (1.0, 0.961, 0.004), (1.1, 0.973, 0.006)]:
        tac_rows.append({"record_type": "hv", "tac": tac, "hv": hv_value, "sd": sd})
    figure_08 = pd.DataFrame(tac_rows)

    ablation_specs = {
        "Social reliability": {"IA-NSGA-III": 0.96, "I-NSGA-III": 0.90, "A-NSGA-III": 0.88, "NSGA-III": 0.82, "NSGA-II": 0.70},
        "Economic efficiency": {"IA-NSGA-III": 0.95, "I-NSGA-III": 0.90, "A-NSGA-III": 0.80, "NSGA-III": 0.76, "NSGA-II": 0.65},
        "Ecological security": {"IA-NSGA-III": 1.00, "I-NSGA-III": 0.998, "A-NSGA-III": 0.94, "NSGA-III": 0.92, "NSGA-II": 0.82},
    }
    speeds = {"IA-NSGA-III": (205, 78), "I-NSGA-III": (190, 70), "A-NSGA-III": (245, 90), "NSGA-III": (270, 110), "NSGA-II": (350, 150)}
    ablation_rows: list[dict[str, object]] = []
    for indicator, variants in ablation_specs.items():
        for variant, plateau in variants.items():
            midpoint, scale = speeds[variant]
            values = 0.08 + (plateau - 0.08) / (1 + np.exp(-(g - midpoint) / scale))
            for generation, value in zip(g, values, strict=True):
                ablation_rows.append({"generation": generation, "indicator": indicator, "variant": variant, "value": value})
    figure_09 = pd.DataFrame(ablation_rows)

    figure_10 = pd.DataFrame(
        [
            {"scenario": scenario, "indicator": indicator, "value": value, "sd": sd}
            for indicator, values, errors in [
                ("Social reliability", [0.942, 0.885, 0.724, 0.625], [0.006, 0.012, 0.025, 0.038]),
                ("Economic efficiency", [0.938, 0.825, 0.684, 0.582], [0.009, 0.018, 0.035, 0.050]),
                ("Ecological security", [0.999, 0.942, 0.895, 0.824], [0.002, 0.017, 0.027, 0.039]),
            ]
            for scenario, value, sd in zip(["Proposed", "No-Marketing", "No-Processing", "Traditional"], values, errors, strict=True)
        ]
    )

    return {
        "figure_02_convergence": figure_02,
        "figure_03_boxplots": figure_03,
        "figure_04_kpis": figure_04,
        "figure_05_pareto": figure_05,
        "figure_06_parameter_sensitivity": figure_06,
        "figure_07_digitalization_sensitivity": figure_07,
        "figure_08_tac_sensitivity": figure_08,
        "figure_09_algorithm_ablation": figure_09,
        "figure_10_module_ablation": figure_10,
    }


def write_calibrated_data(output_dir: str | Path | None = None, seed: int = 1809036, step: int = 10) -> dict[str, Path]:
    target = Path(output_dir) if output_dir else ROOT / "results" / "data"
    target.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, frame in generate_calibrated_data(seed=seed, step=step).items():
        path = target / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path
    return paths
