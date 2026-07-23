from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .calibrated import ALGORITHMS, write_calibrated_data
from .config import ROOT


COLORS = {
    "IA-NSGA-III": "#D73027",
    "NSGA-III": "#2C7BB6",
    "MOEA/D": "#66A61E",
    "NSGA-II": "#E6AB02",
    "I-NSGA-III": "#7B3294",
    "A-NSGA-III": "#1B9E77",
}
MARKERS = {"IA-NSGA-III": "o", "NSGA-III": "s", "MOEA/D": "^", "NSGA-II": "D"}


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 7.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.24,
            "grid.linewidth": 0.6,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "svg.hashsalt": "fishery-ia-nsga3-reproduction",
        }
    )


def _save(fig: plt.Figure, stem: str, output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for extension in formats:
        path = output_dir / f"{stem}.{extension}"
        save_kwargs = {"dpi": dpi, "bbox_inches": "tight"}
        if extension == "svg":
            save_kwargs["metadata"] = {"Date": None}
        fig.savefig(path, **save_kwargs)
        if extension == "svg":
            normalized = "\n".join(
                line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()
            )
            path.write_text(normalized + "\n", encoding="utf-8")
        paths.append(path)
    plt.close(fig)
    return paths


def _box(ax: plt.Axes, xy: tuple[float, float], width: float, height: float, title: str, lines: list[str], color: str) -> None:
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), width, height, boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=1.3, edgecolor=color, facecolor=f"{color}18", transform=ax.transAxes
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height - 0.055, title, ha="center", va="center", weight="bold", color=color, transform=ax.transAxes)
    ax.text(x + 0.025, y + height - 0.105, "\n".join(lines), ha="left", va="top", linespacing=1.45, transform=ax.transAxes)


def figure_01(output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    fig, ax = plt.subplots(figsize=(12, 6.8))
    ax.set_axis_off()
    ax.text(0.5, 0.965, "Improved Adaptive NSGA-III Solver Architecture for PPMS-MOO", ha="center", va="top", fontsize=15, weight="bold", transform=ax.transAxes)
    _box(ax, (0.03, 0.14), 0.24, 0.70, "INPUT PARAMETERS", [
        "Production inputs", "• TAC and fleet capacity", "• Sector structure", "", "Processing inputs", "• Capacity and conversion", "• Cold-chain constraints", "", "Marketing inputs", "• Demand, price, channels"
    ], "#3A8D5D")
    _box(ax, (0.35, 0.49), 0.29, 0.35, "PPMS-MOO COUPLING", [
        "Production  →  Processing", "      ↖              ↓", "Marketing  ←  Logistics", "", "Objectives: F1 · F2 · F3"
    ], "#B8860B")
    _box(ax, (0.35, 0.14), 0.29, 0.24, "IA-NSGA-III", [
        "Logistic chaotic initialization", "Constraint-feedback repair", "Adaptive reference relocation"
    ], "#2878B5")
    _box(ax, (0.72, 0.14), 0.25, 0.70, "OUTPUT PARETO SET", [
        "Feasible allocation X*", "", "Social reliability ηsoc", "Economic efficiency ηecon", "Ecological security ηeco", "", "Policy trade-off scenarios", "Decision-support archive"
    ], "#4C72B0")
    arrows = [((0.27, 0.66), (0.35, 0.66)), ((0.50, 0.49), (0.50, 0.38)), ((0.64, 0.66), (0.72, 0.66)), ((0.64, 0.26), (0.72, 0.32))]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=18, linewidth=1.8, color="#4B5563", transform=ax.transAxes))
    ax.text(0.5, 0.055, "Conceptual recreation of article Figure 1 · DOI 10.3389/fmars.2026.1809036", ha="center", color="#59636E", transform=ax.transAxes)
    return _save(fig, "Figure_01_PPMS_MOO_architecture", output_dir, formats, dpi)


def figure_02(data: pd.DataFrame, output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.4))
    for ax, metric, ylabel in zip(axes, ["HV", "IGD"], ["Hypervolume (HV)", "Inverted Generational Distance (IGD)"], strict=True):
        subset = data[data.metric == metric]
        for algorithm in ALGORITHMS:
            rows = subset[subset.algorithm == algorithm]
            ax.plot(rows.generation, rows.value, color=COLORS[algorithm], lw=2, label=algorithm)
        ax.set(xlabel="Generations", ylabel=ylabel, xlim=(0, 1000))
        ax.legend(frameon=True)
        ax.text(-0.11, -0.18, "a" if metric == "HV" else "b", transform=ax.transAxes, fontsize=11)
    axes[0].set_ylim(0, 1.0)
    axes[1].set_ylim(0, 0.75)
    fig.suptitle("Comparative convergence tracking (processed-data replot)", y=1.02, weight="bold")
    fig.tight_layout()
    return _save(fig, "Figure_02_convergence", output_dir, formats, dpi)


def figure_03(data: pd.DataFrame, output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.4))
    for ax, metric, ylabel in zip(axes, ["HV", "IGD"], ["Hypervolume (HV)", "Inverted Generational Distance (IGD)"], strict=True):
        arrays = [data[(data.metric == metric) & (data.algorithm == alg)].value.to_numpy() for alg in ALGORITHMS]
        result = ax.boxplot(arrays, tick_labels=ALGORITHMS, patch_artist=True, showfliers=True)
        for box, algorithm in zip(result["boxes"], ALGORITHMS, strict=True):
            box.set(facecolor=COLORS[algorithm], alpha=0.55, edgecolor=COLORS[algorithm])
        for median in result["medians"]:
            median.set(color="#222222", linewidth=1.5)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=18)
        ax.text(-0.10, -0.22, "a" if metric == "HV" else "b", transform=ax.transAxes, fontsize=11)
    fig.suptitle("Thirty-run convergence and diversity comparison (reported anchors)", y=1.02, weight="bold")
    fig.tight_layout()
    return _save(fig, "Figure_03_statistical_comparison", output_dir, formats, dpi)


def figure_04(data: pd.DataFrame, output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    indicators = ["Social reliability", "Economic efficiency", "Ecological security"]
    angles = np.linspace(0, 2 * np.pi, len(indicators), endpoint=False)
    closed = np.r_[angles, angles[0]]
    fig, ax = plt.subplots(figsize=(7.0, 6.2), subplot_kw={"projection": "polar"})
    for algorithm in ALGORITHMS:
        ordered = data[data.algorithm == algorithm].set_index("indicator").loc[indicators, "value"].to_numpy()
        values = np.r_[ordered, ordered[0]]
        ax.plot(closed, values, color=COLORS[algorithm], lw=2, marker=MARKERS[algorithm], ms=4, label=algorithm)
        ax.fill(closed, values, color=COLORS[algorithm], alpha=0.06)
    ax.set_xticks(angles, [r"ηsoc", r"ηecon", r"ηeco"])
    ax.set_ylim(0.5, 1.02)
    ax.set_yticks([0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_title("PPM-synergy KPI alignment", pad=22, weight="bold")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.17), ncol=2, frameon=True)
    return _save(fig, "Figure_04_kpi_radar", output_dir, formats, dpi)


def figure_05(data: pd.DataFrame, output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    fig = plt.figure(figsize=(8.0, 6.5))
    ax = fig.add_subplot(111, projection="3d")
    for algorithm, marker in [("IA-NSGA-III", "o"), ("NSGA-III", "s")]:
        rows = data[data.algorithm == algorithm]
        ax.scatter(rows.F1, rows.F2, rows.F3, s=18, marker=marker, color=COLORS[algorithm], alpha=0.78, label=algorithm)
    ax.scatter([1], [1], [1], marker="*", s=180, color="#111111", label="Ideal point (1,1,1)")
    ax.set(xlabel="F1: Social return", ylabel="F2: Economic synergy", zlabel="F3: Ecological security", xlim=(0, 1), ylim=(0, 1), zlim=(0, 1))
    ax.view_init(elev=24, azim=42)
    ax.legend(loc="upper left")
    ax.set_title("Distribution of Pareto-optimal sets (reconstructed)", pad=18, weight="bold")
    return _save(fig, "Figure_05_pareto_sets", output_dir, formats, dpi)


def figure_06(data: pd.DataFrame, output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.4))
    for ax, parameter, xlabel, panel in [
        (axes[0], "adaptive_factor", "Adaptive adjustment factor (γ)", "a"),
        (axes[1], "relocation_frequency", "Relocation frequency (f)", "b"),
    ]:
        rows = data[data.parameter == parameter]
        ax.fill_between(rows.setting, rows.hv - rows.sd, rows.hv + rows.sd, color="#D73027", alpha=0.15)
        ax.plot(rows.setting, rows.hv, color="#222222", marker="o", lw=1.8)
        best = rows.loc[rows.hv.idxmax()]
        ax.scatter([best.setting], [best.hv], marker="*", s=170, color="#F2C14E", edgecolor="#222222", zorder=4)
        ax.set(xlabel=xlabel, ylabel="Hypervolume (HV)", ylim=(0.82, 1.0))
        ax.text(-0.10, -0.18, panel, transform=ax.transAxes, fontsize=11)
    fig.suptitle("IA-NSGA-III parameter sensitivity", y=1.02, weight="bold")
    fig.tight_layout()
    return _save(fig, "Figure_06_parameter_sensitivity", output_dir, formats, dpi)


def figure_07(data: pd.DataFrame, output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    mosaic = [["a", "b"], ["c", "c"]]
    fig, axes = plt.subplot_mosaic(mosaic, figsize=(11.8, 8.0), constrained_layout=True)
    for key, indicator in zip(["a", "b", "c"], ["Social reliability", "Economic efficiency", "Ecological security"], strict=True):
        ax = axes[key]
        for algorithm in ALGORITHMS:
            rows = data[(data.indicator == indicator) & (data.algorithm == algorithm)]
            ax.plot(rows.alpha, rows.value, color=COLORS[algorithm], marker=MARKERS[algorithm], lw=1.7, ms=4, label=algorithm)
        ax.set(xlabel="Digitalization empowerment coefficient (α)", ylabel=indicator, xlim=(1.0, 1.5))
        ax.text(-0.08, -0.16, key, transform=ax.transAxes, fontsize=11)
    axes["a"].legend(frameon=True)
    fig.suptitle("Digitalization sensitivity (reported-trend reconstruction)", weight="bold")
    return _save(fig, "Figure_07_digitalization_sensitivity", output_dir, formats, dpi)


def figure_08(data: pd.DataFrame, output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    fig = plt.figure(figsize=(12.2, 5.2))
    ax1 = fig.add_subplot(121, projection="3d")
    colors = {0.9: "#2166AC", 1.0: "#67A9CF", 1.1: "#D1E5F0"}
    for tac in [0.9, 1.0, 1.1]:
        rows = data[(data.record_type == "pareto") & (data.tac == tac)]
        ax1.scatter(rows.social, rows.economic, rows.ecological, s=10, alpha=0.62, color=colors[tac], label=f"TAC × {tac:.1f}")
    ax1.set(xlabel="ηsoc", ylabel="ηecon", zlabel="ηeco")
    ax1.view_init(elev=26, azim=42)
    ax1.legend(frameon=True)
    ax1.text2D(-0.04, -0.08, "a", transform=ax1.transAxes, fontsize=11)
    ax2 = fig.add_subplot(122)
    hv = data[data.record_type == "hv"].sort_values("tac")
    ax2.errorbar(hv.tac, hv.hv, yerr=hv.sd, color="#1B9E77", marker="o", lw=1.8, capsize=4)
    ax2.set(xlabel="TAC variation coefficient", ylabel="Hypervolume (HV)", xlim=(0.87, 1.13), ylim=(0.93, 0.985))
    ax2.text(-0.10, -0.16, "b", transform=ax2.transAxes, fontsize=11)
    fig.suptitle("Policy-stringency sensitivity", y=1.01, weight="bold")
    fig.tight_layout()
    return _save(fig, "Figure_08_tac_sensitivity", output_dir, formats, dpi)


def figure_09(data: pd.DataFrame, output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    mosaic = [["a", "b"], ["c", "c"]]
    fig, axes = plt.subplot_mosaic(mosaic, figsize=(11.8, 8.0), constrained_layout=True)
    variants = ["IA-NSGA-III", "I-NSGA-III", "A-NSGA-III", "NSGA-III", "NSGA-II"]
    styles = {"IA-NSGA-III": "-", "I-NSGA-III": "--", "A-NSGA-III": "--", "NSGA-III": "-", "NSGA-II": "-"}
    for key, indicator in zip(["a", "b", "c"], ["Social reliability", "Economic efficiency", "Ecological security"], strict=True):
        ax = axes[key]
        for variant in variants:
            rows = data[(data.indicator == indicator) & (data.variant == variant)]
            ax.plot(rows.generation, rows.value, color=COLORS[variant], linestyle=styles[variant], lw=1.8, label=variant)
        ax.set(xlabel="Generations", ylabel=indicator, xlim=(0, 1000), ylim=(0, 1.03))
        ax.text(-0.08, -0.16, key, transform=ax.transAxes, fontsize=11)
    axes["a"].legend(frameon=True)
    fig.suptitle("Algorithm-component ablation", weight="bold")
    return _save(fig, "Figure_09_algorithm_ablation", output_dir, formats, dpi)


def figure_10(data: pd.DataFrame, output_dir: Path, formats: tuple[str, ...], dpi: int) -> list[Path]:
    mosaic = [["a", "b"], ["c", "c"]]
    fig, axes = plt.subplot_mosaic(mosaic, figsize=(11.8, 8.0), constrained_layout=True)
    scenarios = ["Proposed", "No-Marketing", "No-Processing", "Traditional"]
    for key, indicator in zip(["a", "b", "c"], ["Social reliability", "Economic efficiency", "Ecological security"], strict=True):
        ax = axes[key]
        rows = data[data.indicator == indicator].set_index("scenario").loc[scenarios].reset_index()
        bars = ax.bar(rows.scenario, rows.value, yerr=rows.sd, capsize=3, color="#C9252D", edgecolor="#7A1116", alpha=0.96)
        for bar, value in zip(bars, rows.value, strict=True):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.018, f"{value:.3f}", ha="center", fontsize=8)
        ax.set_ylabel(indicator)
        ax.set_ylim(0.4 if indicator != "Ecological security" else 0.7, 1.05)
        ax.tick_params(axis="x", rotation=12)
        ax.text(-0.08, -0.16, key, transform=ax.transAxes, fontsize=11)
    fig.suptitle("Production-processing-marketing module ablation", weight="bold")
    return _save(fig, "Figure_10_module_ablation", output_dir, formats, dpi)


def make_all_figures(
    output_dir: str | Path | None = None,
    data_dir: str | Path | None = None,
    formats: tuple[str, ...] = ("png", "svg"),
    dpi: int = 220,
    seed: int = 1809036,
    step: int = 10,
) -> list[Path]:
    _style()
    figures_dir = Path(output_dir) if output_dir else ROOT / "results" / "processed_data_replots"
    plot_data_dir = Path(data_dir) if data_dir else ROOT / "results" / "data"
    data_paths = write_calibrated_data(plot_data_dir, seed=seed, step=step)
    generated: list[Path] = []
    generated += figure_01(figures_dir, formats, dpi)
    functions = [figure_02, figure_03, figure_04, figure_05, figure_06, figure_07, figure_08, figure_09, figure_10]
    for index, function in enumerate(functions, start=2):
        key = next(name for name in data_paths if name.startswith(f"figure_{index:02d}_"))
        generated += function(pd.read_csv(data_paths[key]), figures_dir, formats, dpi)
    return generated
