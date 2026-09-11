from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from pymoo.indicators.hv import HV
from pymoo.indicators.igd import IGD
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

from fishery_repro.experiment import run_experiment
from fishery_repro.model import OBJECTIVE_NAMES, FisheryPPMSProblem


ROOT = Path(__file__).resolve().parents[1]
STATUS = "calibrated reconstruction; not historical author input"
NEW_RUN_STATUS = "newly executed 30-run surrogate verification; not original author-run logs"

PROVINCES = [
    ("r01", "CN-BJ", "Beijing", "北京"),
    ("r02", "CN-TJ", "Tianjin", "天津"),
    ("r03", "CN-HE", "Hebei", "河北"),
    ("r04", "CN-SX", "Shanxi", "山西"),
    ("r05", "CN-NM", "Inner Mongolia", "内蒙古"),
    ("r06", "CN-LN", "Liaoning", "辽宁"),
    ("r07", "CN-JL", "Jilin", "吉林"),
    ("r08", "CN-HL", "Heilongjiang", "黑龙江"),
    ("r09", "CN-SH", "Shanghai", "上海"),
    ("r10", "CN-JS", "Jiangsu", "江苏"),
    ("r11", "CN-ZJ", "Zhejiang", "浙江"),
    ("r12", "CN-AH", "Anhui", "安徽"),
    ("r13", "CN-FJ", "Fujian", "福建"),
    ("r14", "CN-JX", "Jiangxi", "江西"),
    ("r15", "CN-SD", "Shandong", "山东"),
    ("r16", "CN-HA", "Henan", "河南"),
    ("r17", "CN-HB", "Hubei", "湖北"),
    ("r18", "CN-HN", "Hunan", "湖南"),
    ("r19", "CN-GD", "Guangdong", "广东"),
    ("r20", "CN-GX", "Guangxi", "广西"),
    ("r21", "CN-HI", "Hainan", "海南"),
    ("r22", "CN-CQ", "Chongqing", "重庆"),
    ("r23", "CN-SC", "Sichuan", "四川"),
    ("r24", "CN-GZ", "Guizhou", "贵州"),
    ("r25", "CN-YN", "Yunnan", "云南"),
    ("r26", "CN-XZ", "Tibet", "西藏"),
    ("r27", "CN-SN", "Shaanxi", "陕西"),
    ("r28", "CN-GS", "Gansu", "甘肃"),
    ("r29", "CN-QH", "Qinghai", "青海"),
    ("r30", "CN-NX", "Ningxia", "宁夏"),
    ("r31", "CN-XJ", "Xinjiang", "新疆"),
]

SECTORS = [
    (1, "marine_capture", "海洋捕捞"),
    (2, "freshwater_capture", "淡水捕捞"),
    (3, "marine_aquaculture", "海水养殖"),
    (4, "freshwater_aquaculture", "淡水养殖"),
]
MODES = [(1, "fresh_sales", "鲜销"), (2, "deep_processing", "深加工")]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_input_tables(target: Path) -> dict[str, list[dict[str, object]]]:
    target.mkdir(parents=True, exist_ok=True)
    problem = FisheryPPMSProblem(seed=1809036)
    province_rows: list[dict[str, object]] = []
    matrix_rows: list[dict[str, object]] = []

    for index, (region_id, code, province_en, province_zh) in enumerate(PROVINCES):
        province_rows.append(
            {
                "region_id": region_id,
                "province_code": code,
                "province_en": province_en,
                "province_zh": province_zh,
                "region_share_proxy": problem.region_share[index],
                "digital_index_proxy": problem.digital_index[index],
                "workforce_proxy_people": problem.workforce[index],
                "cold_capacity_proxy_tonnes": problem.cold_capacity[index],
                "power_capacity_proxy_kw": problem.power_capacity[index],
                "mapping_note": "NBS standard province order assigned for reconstruction; original r-index order unavailable",
                "data_status": STATUS,
            }
        )
        for sector_index, (sector_id, sector_en, sector_zh) in enumerate(SECTORS):
            for mode_index, (mode_id, mode_en, mode_zh) in enumerate(MODES):
                matrix_rows.append(
                    {
                        "variable_id": f"x_{region_id}_s{sector_id}_m{mode_id}",
                        "region_id": region_id,
                        "province_code": code,
                        "province_en": province_en,
                        "province_zh": province_zh,
                        "sector_id": sector_id,
                        "sector_en": sector_en,
                        "sector_zh": sector_zh,
                        "mode_id": mode_id,
                        "mode_en": mode_en,
                        "mode_zh": mode_zh,
                        "upper_bound_proxy_tonnes": problem.ub_amount[index, sector_index, mode_index],
                        "region_share_proxy": problem.region_share[index],
                        "digital_index_proxy": problem.digital_index[index],
                        "workforce_proxy_people": problem.workforce[index],
                        "cold_capacity_proxy_tonnes": problem.cold_capacity[index],
                        "power_capacity_proxy_kw": problem.power_capacity[index],
                        "income_coefficient_proxy": problem.income_coeff[sector_index, mode_index],
                        "marginal_value_coefficient_proxy": problem.value_coeff[sector_index, mode_index],
                        "supply_chain_cost_coefficient_proxy": problem.cost_coeff[sector_index, mode_index],
                        "ecological_weight_proxy": problem.eco_coeff[sector_index, mode_index],
                        "fleet_power_coefficient_proxy": problem.power_coeff[sector_index],
                        "data_status": STATUS,
                    }
                )

    sector_rows: list[dict[str, object]] = []
    for sector_index, (sector_id, sector_en, sector_zh) in enumerate(SECTORS):
        for mode_index, (mode_id, mode_en, mode_zh) in enumerate(MODES):
            sector_rows.append(
                {
                    "sector_id": sector_id,
                    "sector_en": sector_en,
                    "sector_zh": sector_zh,
                    "mode_id": mode_id,
                    "mode_en": mode_en,
                    "mode_zh": mode_zh,
                    "income_coefficient_proxy": problem.income_coeff[sector_index, mode_index],
                    "marginal_value_coefficient_proxy": problem.value_coeff[sector_index, mode_index],
                    "supply_chain_cost_coefficient_proxy": problem.cost_coeff[sector_index, mode_index],
                    "ecological_weight_proxy": problem.eco_coeff[sector_index, mode_index],
                    "fleet_power_coefficient_proxy": problem.power_coeff[sector_index],
                    "data_status": STATUS,
                }
            )

    national_rows = [
        {"parameter": "baseline_total", "value": 71_161_716.0, "unit": "tonnes", "role": "2023 production anchor", "source": "Paper Table 3", "data_status": "article transcription"},
        {"parameter": "catch_limit", "value": problem.catch_limit, "unit": "tonnes", "role": "national capture constraint in surrogate", "source": "Model proxy aligned to 2023 national total capture", "data_status": STATUS},
        {"parameter": "total_limit", "value": problem.total_limit, "unit": "tonnes", "role": "110% of production anchor", "source": "deterministic model rule", "data_status": STATUS},
        {"parameter": "processing_limit", "value": problem.processing_limit, "unit": "tonnes", "role": "37% of production anchor", "source": "deterministic model rule", "data_status": STATUS},
        {"parameter": "minimum_supply", "value": problem.minimum_supply, "unit": "tonnes", "role": "58% of production anchor", "source": "deterministic model rule", "data_status": STATUS},
        {"parameter": "power_limit", "value": problem.power_limit, "unit": "kW", "role": "2023 fleet-power anchor", "source": "Paper Table 3", "data_status": "article transcription"},
        {"parameter": "capture_share_max", "value": 0.28, "unit": "ratio", "role": "constraint threshold", "source": "public surrogate implementation", "data_status": STATUS},
        {"parameter": "hv_reference_1", "value": 1.05, "unit": "cost-space score", "role": "new-run HV reference point", "source": "declared replacement metric method", "data_status": NEW_RUN_STATUS},
        {"parameter": "hv_reference_2", "value": 1.05, "unit": "cost-space score", "role": "new-run HV reference point", "source": "declared replacement metric method", "data_status": NEW_RUN_STATUS},
        {"parameter": "hv_reference_3", "value": 1.05, "unit": "cost-space score", "role": "new-run HV reference point", "source": "declared replacement metric method", "data_status": NEW_RUN_STATUS},
    ]

    dictionary_rows = [
        {"field": "region_share_proxy", "meaning": "Deterministic regional share used to distribute the national production anchor", "unit": "ratio", "original_available": "no", "construction": "Seeded proxy generated in FisheryPPMSProblem(seed=1809036)"},
        {"field": "digital_index_proxy", "meaning": "Proxy for the regional EWM digitalisation index described in the manuscript", "unit": "0-1 score", "original_available": "no", "construction": "Deterministic spatial gradient plus seeded perturbation; not EWM observations"},
        {"field": "workforce_proxy_people", "meaning": "Regional fishery workforce denominator", "unit": "people", "original_available": "no", "construction": "National proxy distributed by region share with seeded perturbation"},
        {"field": "cold_capacity_proxy_tonnes", "meaning": "Regional processing/cold-chain capacity", "unit": "tonnes", "original_available": "no", "construction": "National production anchor multiplied by region share and proxy cold-chain intensity"},
        {"field": "power_capacity_proxy_kw", "meaning": "Regional fleet-power capacity", "unit": "kW", "original_available": "no", "construction": "2023 national power anchor distributed by region share with seeded perturbation"},
        {"field": "upper_bound_proxy_tonnes", "meaning": "Maximum decoded allocation for one region-sector-mode decision variable", "unit": "tonnes", "original_available": "no", "construction": "baseline_total x 1.20 x region share x sector share x mode share"},
        {"field": "income_coefficient_proxy", "meaning": "Unit social-income coefficient", "unit": "normalized coefficient", "original_available": "no", "construction": "Explicit 4x2 surrogate coefficient table"},
        {"field": "marginal_value_coefficient_proxy", "meaning": "Processing/marketing marginal output value", "unit": "normalized coefficient", "original_available": "no", "construction": "Explicit 4x2 surrogate coefficient table"},
        {"field": "supply_chain_cost_coefficient_proxy", "meaning": "Processing and cold-chain/logistics cost", "unit": "normalized coefficient", "original_available": "no", "construction": "Explicit 4x2 surrogate coefficient table"},
        {"field": "ecological_weight_proxy", "meaning": "Relative ecological desirability weight", "unit": "normalized coefficient", "original_available": "no", "construction": "Explicit 4x2 surrogate coefficient table"},
        {"field": "fleet_power_coefficient_proxy", "meaning": "Sector-specific fleet-power intensity", "unit": "relative coefficient", "original_available": "no", "construction": "Explicit 4-element surrogate coefficient vector"},
    ]

    frames = {
        "province_inputs": pd.DataFrame(province_rows),
        "coefficient_matrix_248_rows": pd.DataFrame(matrix_rows),
        "sector_mode_coefficients": pd.DataFrame(sector_rows),
        "national_constraints": pd.DataFrame(national_rows),
        "variable_dictionary": pd.DataFrame(dictionary_rows),
    }
    for name, frame in frames.items():
        frame.to_csv(target / f"{name}.csv", index=False, encoding="utf-8-sig")
    return {name: frame.to_dict("records") for name, frame in frames.items()}


def build_metric_audit(run_dir: Path) -> None:
    solutions = pd.read_csv(run_dir / "final_population_objectives_constraints.csv")
    summary = pd.read_csv(run_dir / "run_summary.csv")
    objective_columns = list(OBJECTIVE_NAMES)
    feasible = solutions[solutions["feasible"]].copy()
    source = feasible if not feasible.empty else solutions
    pooled_cost = 1 - np.clip(source[objective_columns].to_numpy(float), 0, 1)
    reference_ids = NonDominatedSorting().do(pooled_cost, only_non_dominated_front=True)
    reference_front = pooled_cost[reference_ids]
    reference_frame = pd.DataFrame(reference_front, columns=[f"cost_{name}" for name in objective_columns])
    reference_frame.insert(0, "reference_point_id", np.arange(1, len(reference_frame) + 1))
    reference_frame["data_status"] = NEW_RUN_STATUS
    reference_frame.to_csv(run_dir / "pooled_reference_front.csv", index=False)

    hv = HV(ref_point=np.full(3, 1.05))
    igd = IGD(reference_front)
    checks: list[dict[str, object]] = []
    for row in summary.to_dict("records"):
        selected = solutions[(solutions["algorithm"] == row["algorithm"]) & (solutions["run_id"] == row["run_id"])]
        feasible_selected = selected[selected["feasible"]]
        metric_source = feasible_selected if not feasible_selected.empty else selected
        costs = 1 - np.clip(metric_source[objective_columns].to_numpy(float), 0, 1)
        hv_value = float(hv(costs))
        igd_value = float(igd(costs))
        checks.append(
            {
                "algorithm": row["algorithm"],
                "run_id": int(row["run_id"]),
                "seed": int(row["seed"]),
                "stored_hv": row["hypervolume"],
                "recomputed_hv": hv_value,
                "hv_abs_difference": abs(hv_value - row["hypervolume"]),
                "stored_igd": row["igd_to_pooled_reference"],
                "recomputed_igd": igd_value,
                "igd_abs_difference": abs(igd_value - row["igd_to_pooled_reference"]),
                "metric_population": "feasible" if not feasible_selected.empty else "all_no_feasible",
                "data_status": NEW_RUN_STATUS,
            }
        )
    pd.DataFrame(checks).to_csv(run_dir / "metric_recomputation_check.csv", index=False)
    metric_definition = {
        "data_status": NEW_RUN_STATUS,
        "objective_direction": "three maximisation scores converted to minimisation costs using cost=1-score",
        "objectives": objective_columns,
        "hv_reference_point_cost_space": [1.05, 1.05, 1.05],
        "igd_reference": "pooled non-dominated front from this new experiment",
        "reference_front_file": "pooled_reference_front.csv",
        "feasibility_rule": "use feasible final solutions when available; otherwise use all and flag fallback",
        "important_limitation": "The article's original normalisation, HV reference point, IGD reference front and run outputs are unavailable.",
    }
    (run_dir / "metric_definition.json").write_text(json.dumps(metric_definition, indent=2), encoding="utf-8")


def copy_sources(package_root: Path) -> None:
    source_dir = package_root / "data" / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    sources = [
        *(ROOT / "data" / "paper").glob("*.csv"),
        ROOT / "data" / "public" / "source_catalog.csv",
        ROOT / "data" / "public" / "moa_national_fishery_statistics.csv",
        ROOT / "data" / "public" / "moa_2024_detailed_fishery_statistics.csv",
        ROOT / "data" / "public" / "moa_fishery_environment_2024.csv",
        ROOT / "data" / "public" / "official_latest_aquatic_products_2025.csv",
        ROOT / "data" / "public" / "world_bank_fao_china_fisheries_2014_2023.csv",
        ROOT / "data" / "verified" / "official_2023_summary.csv",
    ]
    for source in sources:
        shutil.copy2(source, source_dir / source.name)

    calibrated_dir = package_root / "runs" / "article_figure3_calibrated"
    calibrated_dir.mkdir(parents=True, exist_ok=True)
    calibrated = pd.read_csv(ROOT / "results" / "data" / "figure_03_boxplots.csv")
    calibrated["data_status"] = "calibrated reconstruction from manuscript anchors; not original run logs"
    calibrated["generation_method"] = "deterministic normal draws from disclosed mean/dispersion anchors; seed 1809036"
    calibrated.to_csv(calibrated_dir / "figure_03_calibrated_30run_metrics.csv", index=False)
    shutil.copy2(ROOT / "src" / "fishery_repro" / "calibrated.py", calibrated_dir / "generation_code_calibrated.py")


def build_payload(package_root: Path, tables: dict[str, list[dict[str, object]]]) -> None:
    source_catalog = pd.read_csv(ROOT / "data" / "public" / "source_catalog.csv").fillna("")
    availability = pd.read_csv(package_root / "02_Material_Availability.csv").fillna("")
    payload = {
        **tables,
        "source_map": source_catalog.to_dict("records"),
        "availability": availability.to_dict("records"),
        "metadata": {
            "prepared_on": "2026-09-11",
            "paper_doi": "10.3389/fmars.2026.1809036",
            "package_disclosure": "Replacement evidence only; no historical original matrix or run log is represented as recovered.",
            "nbs_a0407_check": "Official page returned HTTP 403 on 2026-09-11; no values copied from third-party aggregators.",
        },
    }
    (package_root / "workbook_payload.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, default=ROOT / "editor_response")
    parser.add_argument("--skip-experiment", action="store_true")
    args = parser.parse_args()
    package_root = args.package_root.resolve()
    reconstructed = package_root / "data" / "reconstructed"
    tables = build_input_tables(reconstructed)
    copy_sources(package_root)

    run_dir = package_root / "runs" / "new_30run_surrogate"
    if not args.skip_experiment:
        run_experiment(ROOT / "configs" / "experiments" / "editor_response_30run.yaml", run_dir)
    if not (run_dir / "run_summary.csv").exists():
        raise FileNotFoundError("Run the replacement experiment before metric audit")
    build_metric_audit(run_dir)
    build_payload(package_root, tables)

    code_dir = package_root / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    for source in [
        ROOT / "configs" / "experiments" / "editor_response_30run.yaml",
        ROOT / "scripts" / "build_editor_response_data.py",
        ROOT / "scripts" / "build_editor_response_workbook.mjs",
        ROOT / "scripts" / "build_editor_response_letter.py",
        ROOT / "scripts" / "convert_docx_with_word.ps1",
        ROOT / "scripts" / "package_editor_response.py",
        ROOT / "src" / "fishery_repro" / "model.py",
        ROOT / "src" / "fishery_repro" / "experiment.py",
        ROOT / "src" / "fishery_repro" / "benchmark.py",
    ]:
        if source.exists():
            shutil.copy2(source, code_dir / source.name)

    print(json.dumps({"package_root": str(package_root), "run_rows": len(pd.read_csv(run_dir / "run_summary.csv")), "reference_front_rows": len(pd.read_csv(run_dir / "pooled_reference_front.csv"))}, indent=2))


if __name__ == "__main__":
    main()
