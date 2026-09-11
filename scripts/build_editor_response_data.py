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
    public_panel = problem.public_panel.reset_index(drop=True)
    province_rows: list[dict[str, object]] = []
    matrix_rows: list[dict[str, object]] = []

    for index, (region_id, code, province_en, province_zh) in enumerate(PROVINCES):
        public = public_panel.iloc[index]
        if public["province_code"] != code:
            raise ValueError(
                f"Province order mismatch at row {index + 1}: {public['province_code']} != {code}"
            )
        province_rows.append(
            {
                "region_id": region_id,
                "province_code": code,
                "province_en": province_en,
                "province_zh": province_zh,
                "year": int(public["year"]),
                "aquatic_total_official_10000_t": public["aquatic_total_10000_t"],
                "marine_capture_official_10000_t": public["marine_capture_10000_t"],
                "freshwater_capture_official_10000_t": public["freshwater_capture_10000_t"],
                "marine_aquaculture_official_10000_t": public["marine_aquaculture_10000_t"],
                "freshwater_aquaculture_official_10000_t": public["freshwater_aquaculture_10000_t"],
                "population_official_10000_persons": public["population_10000_persons"],
                "disposable_income_official_yuan": public["disposable_income_yuan"],
                "wastewater_cod_official_tonnes": public["wastewater_cod_tonnes"],
                "wastewater_phosphorus_official_tonnes": public["wastewater_total_phosphorus_tonnes"],
                "freight_official_10000_tonnes": public["freight_total_10000_tonnes"],
                "enterprises_official_units": public["enterprises_units"],
                "ecommerce_enterprises_official_units": public["ecommerce_enterprises_units"],
                "ecommerce_sales_official_100m_yuan": public["ecommerce_sales_100m_yuan"],
                "ecommerce_adoption_rate_processed": problem.ecommerce_adoption_rate[index],
                "region_share_processed": problem.region_share[index],
                "paper_2023_calibration_factor": problem.paper_calibration_factor,
                "digital_index_processed": problem.digital_index[index],
                "income_multiplier_processed": problem.income_multiplier[index],
                "social_need_multiplier_processed": problem.social_need_multiplier[index],
                "ecological_pressure_index_processed": problem.ecological_pressure_index[index],
                "freight_index_processed": problem.freight_index[index],
                "workforce_processed_people": problem.workforce[index],
                "cold_capacity_processed_tonnes": problem.cold_capacity[index],
                "power_capacity_processed_kw": problem.power_capacity[index],
                "mapping_note": "NBS standard province order assigned for reconstruction; original r-index order unavailable",
                "official_data_status": "official public 2024 NBS transcription; not historical author input",
                "derived_data_status": STATUS,
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
                        "official_2024_sector_tonnes": problem.observed_2024_sector_tonnes[index, sector_index],
                        "paper_calibrated_sector_tonnes": problem.calibrated_sector_tonnes[index, sector_index],
                        "assumed_mode_share": problem.mode_share_by_sector[sector_index, mode_index],
                        "baseline_sector_mode_processed_tonnes": problem.baseline_sector_mode_tonnes[index, sector_index, mode_index],
                        "upper_bound_processed_tonnes": problem.ub_amount[index, sector_index, mode_index],
                        "region_share_processed": problem.region_share[index],
                        "digital_index_processed": problem.digital_index[index],
                        "income_multiplier_processed": problem.income_multiplier[index],
                        "social_need_multiplier_processed": problem.social_need_multiplier[index],
                        "ecological_pressure_index_processed": problem.ecological_pressure_index[index],
                        "ecological_quality_multiplier_processed": problem.ecological_quality_multiplier[index],
                        "freight_index_processed": problem.freight_index[index],
                        "logistics_cost_multiplier_processed": problem.logistics_cost_multiplier[index],
                        "workforce_processed_people": problem.workforce[index],
                        "cold_capacity_processed_tonnes": problem.cold_capacity[index],
                        "power_capacity_processed_kw": problem.power_capacity[index],
                        "income_coefficient_proxy": problem.income_coeff[sector_index, mode_index],
                        "marginal_value_coefficient_proxy": problem.value_coeff[sector_index, mode_index],
                        "supply_chain_cost_coefficient_proxy": problem.cost_coeff[sector_index, mode_index],
                        "ecological_weight_proxy": problem.eco_coeff[sector_index, mode_index],
                        "fleet_power_coefficient_proxy": problem.power_coeff[sector_index],
                        "official_source": "NBS China Statistical Yearbook 2025, Table 12-15",
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
                    "assumed_mode_share": problem.mode_share_by_sector[sector_index, mode_index],
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
        {"parameter": "nbs_2024_31province_sector_sum", "value": problem.observed_2024_sector_tonnes.sum(), "unit": "tonnes", "role": "official public regional-sector backbone", "source": "NBS 2025 Table 12-15", "data_status": "official public 2024 NBS transcription; not historical author input"},
        {"parameter": "paper_calibration_factor", "value": problem.paper_calibration_factor, "unit": "ratio", "role": "scale 2024 public sector pattern to the paper's 2023 national production anchor", "source": "71,161,716 / sum of four NBS provincial sectors", "data_status": STATUS},
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
        {"field": "*_official_*", "meaning": "Values transcribed from the six 2024 NBS province tables", "unit": "as named", "original_available": "public replacement only", "construction": "Direct transcription; no interpolation; official URLs retained in the source data dictionary"},
        {"field": "official_2024_sector_tonnes", "meaning": "Province-sector output before paper calibration", "unit": "tonnes", "original_available": "public replacement only", "construction": "NBS Table 12-15 printed value x 10,000"},
        {"field": "paper_calibrated_sector_tonnes", "meaning": "Official 2024 province-sector pattern scaled to the paper's 2023 total", "unit": "tonnes", "original_available": "no", "construction": "official_2024_sector_tonnes x 71,161,716 / sum(all official province-sector tonnes)"},
        {"field": "assumed_mode_share", "meaning": "Sector-specific split between fresh sales and deep processing", "unit": "ratio", "original_available": "no", "construction": "Declared assumptions: capture 62/38 and 67/33; aquaculture 74/26 and 78/22"},
        {"field": "region_share_processed", "meaning": "Regional share of the four official aquatic-product sectors", "unit": "ratio", "original_available": "no", "construction": "Calibrated province total divided by 71,161,716; sums to one"},
        {"field": "digital_index_processed", "meaning": "External proxy for the unreleased regional EWM fishery digitalisation index", "unit": "0-1 score", "original_available": "no", "construction": "0.25 + 0.70 x [0.60 minmax(e-commerce adoption) + 0.40 minmax(log(1+sales/enterprise))]"},
        {"field": "income_multiplier_processed", "meaning": "Regional economic-value multiplier", "unit": "ratio", "original_available": "no", "construction": "2024 provincial disposable income / 2024 national average; clipped to 0.65-1.45"},
        {"field": "social_need_multiplier_processed", "meaning": "Inverse-income social-need adjustment", "unit": "ratio", "original_available": "no", "construction": "2024 national disposable-income average / province income; clipped to 0.65-1.45"},
        {"field": "ecological_pressure_index_processed", "meaning": "External wastewater-pressure proxy; not a fishery-water-quality measure", "unit": "0-1 score", "original_available": "no", "construction": "minmax(log(1 + (COD + 20 x total phosphorus) / population))"},
        {"field": "freight_index_processed", "meaning": "External logistics-capacity proxy", "unit": "0-1 score", "original_available": "no", "construction": "minmax(log(1 + regional freight tonnage))"},
        {"field": "workforce_processed_people", "meaning": "Regional fishery workforce denominator", "unit": "people", "original_available": "no", "construction": "11,762,300 distributed with 75% production share and 25% population share"},
        {"field": "cold_capacity_processed_tonnes", "meaning": "Regional processing/cold-chain capacity", "unit": "tonnes", "original_available": "no", "construction": "Calibrated province production x (0.18 + 0.22 x freight index)"},
        {"field": "power_capacity_processed_kw", "meaning": "Regional fleet-power capacity", "unit": "kW", "original_available": "no", "construction": "18,940,154 distributed by calibrated capture output plus 5% of total output"},
        {"field": "upper_bound_processed_tonnes", "meaning": "Maximum decoded allocation for one region-sector-mode decision variable", "unit": "tonnes", "original_available": "no", "construction": "1.20 x calibrated province-sector output x assumed utilisation-mode share"},
        {"field": "income_coefficient_proxy", "meaning": "Unit social-income coefficient", "unit": "normalized coefficient", "original_available": "no", "construction": "Explicit 4x2 surrogate coefficient table"},
        {"field": "marginal_value_coefficient_proxy", "meaning": "Processing/marketing marginal output value", "unit": "normalized coefficient", "original_available": "no", "construction": "Explicit 4x2 surrogate coefficient table"},
        {"field": "supply_chain_cost_coefficient_proxy", "meaning": "Processing and cold-chain/logistics cost", "unit": "normalized coefficient", "original_available": "no", "construction": "Explicit 4x2 surrogate coefficient table"},
        {"field": "ecological_weight_proxy", "meaning": "Relative ecological desirability weight", "unit": "normalized coefficient", "original_available": "no", "construction": "Explicit 4x2 surrogate coefficient table"},
        {"field": "fleet_power_coefficient_proxy", "meaning": "Sector-specific fleet-power intensity", "unit": "relative coefficient", "original_available": "no", "construction": "Explicit 4-element surrogate coefficient vector"},
    ]

    derivation_rows = [
        {"step": 1, "output": "official_2024_sector_tonnes", "formula": "NBS Table 12-15 value x 10,000", "inputs": "six official NBS province tables", "evidence_class": "official public data", "limitation": "2024 replacement evidence; not the historical model workbook"},
        {"step": 2, "output": "paper_calibrated_sector_tonnes", "formula": "official sector tonnes x 71,161,716 / official 31-province sector sum", "inputs": "NBS 2024 sector pattern + paper Table 3 total", "evidence_class": "processed/calibrated", "limitation": "Assumes the 2024 spatial-sector pattern is an acceptable proxy for 2023"},
        {"step": 3, "output": "baseline_sector_mode_processed_tonnes", "formula": "calibrated sector tonnes x declared fresh/deep mode share", "inputs": "step 2 + four stated mode splits", "evidence_class": "processed/calibrated", "limitation": "Province-by-mode historical data are unavailable"},
        {"step": 4, "output": "upper_bound_processed_tonnes", "formula": "1.20 x baseline sector-mode tonnes", "inputs": "step 3", "evidence_class": "processed/calibrated", "limitation": "The 20% headroom is a public-surrogate modelling choice"},
        {"step": 5, "output": "digital_index_processed", "formula": "0.25 + 0.70 x weighted min-max e-commerce composite", "inputs": "NBS enterprise counts and e-commerce sales", "evidence_class": "processed proxy", "limitation": "External enterprise proxy; not the paper's unreleased fishery EWM index"},
        {"step": 6, "output": "economic/social multipliers", "formula": "income / national average and its inverse; clipped", "inputs": "NBS per-capita disposable income", "evidence_class": "processed proxy", "limitation": "Household income is not a fishery-specific wage series"},
        {"step": 7, "output": "ecological_pressure_index_processed", "formula": "min-max log of (COD + 20 x phosphorus) per population", "inputs": "NBS preliminary wastewater and population data", "evidence_class": "processed proxy", "limitation": "General wastewater pressure is not fishery habitat condition"},
        {"step": 8, "output": "freight/cold-chain fields", "formula": "log-minmax freight; production x (0.18 + 0.22 x freight index)", "inputs": "NBS freight + calibrated production", "evidence_class": "processed proxy", "limitation": "Freight is economy-wide and cold-chain capacity remains inferred"},
        {"step": 9, "output": "workforce/power fields", "formula": "national anchors distributed by disclosed weights", "inputs": "paper/MOA anchors + public production and population", "evidence_class": "processed proxy", "limitation": "No original province allocation file was retained"},
    ]

    public_qc_specs = [
        ("aquatic_total", "aquatic_total_10000_t", 7357.6, 0.31, "rounding"),
        ("marine_total", "marine_total_10000_t", 3708.9, 0.31, "rounding"),
        ("marine_capture", "marine_capture_10000_t", 1181.2, 0.31, "rounding"),
        ("marine_aquaculture", "marine_aquaculture_10000_t", 2527.6, 0.31, "rounding"),
        ("freshwater_total", "freshwater_total_10000_t", 3648.7, 0.31, "rounding"),
        ("freshwater_capture", "freshwater_capture_10000_t", 116.3, 0.31, "rounding"),
        ("freshwater_aquaculture", "freshwater_aquaculture_10000_t", 3532.4, 0.31, "rounding"),
        ("population", "population_10000_persons", 140828.0, 200.0, "national includes 2 million military personnel excluded from province rows"),
        ("wastewater_cod", "wastewater_cod_tonnes", 27998827.0, 1.0, "printed whole-number rounding"),
        ("wastewater_total_phosphorus", "wastewater_total_phosphorus_tonnes", 390481.0, 3.0, "printed whole-number rounding"),
        ("freight_total", "freight_total_10000_tonnes", 5783625.0, 97072.0, "national includes 97,072 not classified by region"),
        ("enterprises", "enterprises_units", 1605346.0, 0.0, "exact reconciliation"),
        ("ecommerce_enterprises", "ecommerce_enterprises_units", 205026.0, 0.0, "exact reconciliation"),
        ("ecommerce_sales", "ecommerce_sales_100m_yuan", 386544.0, 0.21, "one-decimal rounding"),
    ]
    public_qc_rows = []
    for metric, column, national, tolerance, explanation in public_qc_specs:
        province_sum = float(public_panel[column].sum())
        difference = province_sum - national
        public_qc_rows.append(
            {
                "metric": metric,
                "province_sum": province_sum,
                "national_printed_value": national,
                "difference": difference,
                "allowed_absolute_difference": tolerance,
                "result": "PASS" if abs(abs(difference) - tolerance) < 1e-9 or abs(difference) <= tolerance + 1e-9 else "FAIL",
                "difference_explanation": explanation,
            }
        )

    frames = {
        "official_2024_panel": public_panel,
        "public_data_qc": pd.DataFrame(public_qc_rows),
        "province_inputs": pd.DataFrame(province_rows),
        "coefficient_matrix_248_rows": pd.DataFrame(matrix_rows),
        "sector_mode_coefficients": pd.DataFrame(sector_rows),
        "national_constraints": pd.DataFrame(national_rows),
        "variable_dictionary": pd.DataFrame(dictionary_rows),
        "derivation_rules": pd.DataFrame(derivation_rows),
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
        ROOT / "data" / "public" / "nbs_2024_31_province_public_panel.csv",
        ROOT / "data" / "public" / "nbs_2024_31_province_public_panel_dictionary.csv",
        ROOT / "data" / "public" / "nbs_2024_national_benchmarks.csv",
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
            "nbs_public_panel": "Six official NBS China Statistical Yearbook 2025 tables were transcribed for all 31 province-level regions; production is observed public data and model-specific coefficients remain processed/calibrated.",
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
