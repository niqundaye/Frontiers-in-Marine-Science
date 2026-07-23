from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import ROOT


PAPER_DATA = ROOT / "data" / "paper"
VERIFIED_DATA = ROOT / "data" / "verified"


def load_table(number: int) -> pd.DataFrame:
    matches = sorted(PAPER_DATA.glob(f"table_{number}_*.csv"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one CSV for paper table {number}, found {matches}")
    return pd.read_csv(matches[0])


def load_official_2023() -> pd.DataFrame:
    return pd.read_csv(VERIFIED_DATA / "official_2023_summary.csv")


def audit_tables() -> pd.DataFrame:
    economic = load_table(2)
    capacity = load_table(3)
    checks: list[dict[str, object]] = []

    component_sum = economic[
        ["capture_value", "aquaculture_value", "processing_value", "circulation_service"]
    ].sum(axis=1)
    for year, reported, calculated in zip(
        economic["year"], economic["total_economic_output"], component_sum, strict=True
    ):
        checks.append(
            {
                "check": "table_2_component_sum",
                "year": int(year),
                "reported": float(reported),
                "calculated": float(calculated),
                "difference": float(reported - calculated),
                "status": "pass" if abs(reported - calculated) <= 1 else "review",
            }
        )

    row_2023 = capacity.loc[capacity["year"] == 2023].iloc[0]
    official = load_official_2023().set_index("indicator")
    mappings = {
        "total_production_tonnes": "total_aquatic_products",
        "marine_aquaculture_tonnes": "marine_aquaculture",
        "domestic_capture_tonnes": "domestic_marine_capture",
        "distant_water_capture_tonnes": "distant_water_capture",
        "processing_enterprises": "processing_enterprises",
        "cold_storage_units": "cold_storage_units",
        "fleet_power_kw": "fleet_power",
    }
    for paper_col, official_key in mappings.items():
        reported = float(row_2023[paper_col])
        expected = float(official.loc[official_key, "value"])
        relative = abs(reported - expected) / max(abs(expected), 1.0)
        checks.append(
            {
                "check": f"official_2023_{paper_col}",
                "year": 2023,
                "reported": reported,
                "calculated": expected,
                "difference": reported - expected,
                "status": "pass" if relative <= 5e-5 else "review",
            }
        )
    return pd.DataFrame(checks)


def write_audit(output: str | Path | None = None) -> Path:
    target = Path(output) if output else ROOT / "results" / "tables" / "data_audit.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    audit_tables().to_csv(target, index=False)
    return target

