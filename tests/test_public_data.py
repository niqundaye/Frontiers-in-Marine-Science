from pathlib import Path

import pandas as pd

from fishery_repro.config import ROOT
from fishery_repro.public_data import WORLD_BANK_INDICATORS, source_catalog


PUBLIC = ROOT / "data" / "public"


def test_world_bank_snapshot_has_three_complete_ten_year_series():
    frame = pd.read_csv(PUBLIC / "world_bank_fao_china_fisheries_2014_2023.csv")
    assert set(frame.indicator_code) == set(WORLD_BANK_INDICATORS)
    assert set(frame.year) == set(range(2014, 2024))
    assert frame.groupby("indicator_code").size().eq(10).all()
    assert frame.value.notna().all()


def test_moa_snapshot_keeps_source_and_parse_status():
    frame = pd.read_csv(PUBLIC / "moa_national_fishery_statistics.csv")
    assert {2015, 2016, 2019, 2020, 2021, 2022, 2023, 2024}.issubset(set(frame.year))
    assert frame.source_url.str.startswith("https://").all()
    assert frame.extraction_status.isin(["parsed", "not_found"]).all()
    assert (frame.extraction_status == "parsed").mean() >= 0.75


def test_catalog_marks_unavailable_province_data_without_imputation():
    catalog = source_catalog("2026-07-23")
    nbs = catalog[catalog.source_id == "nbs_a0407"].iloc[0]
    assert "403" in nbs.access
    assert not nbs.repository_file


def _value(frame: pd.DataFrame, indicator: str, category: str = "total") -> float:
    row = frame[(frame.indicator == indicator) & (frame.category == category)]
    assert len(row) == 1, (indicator, category, len(row))
    return float(row.iloc[0].value)


def test_moa_2024_detailed_snapshot_is_normalized_and_reconciles():
    frame = pd.read_csv(PUBLIC / "moa_2024_detailed_fishery_statistics.csv")
    assert len(frame) == 99
    assert frame.source_sha256.str.fullmatch(r"[0-9a-f]{64}").all()
    assert frame.data_label.eq("经过处理的数据（公开来源）").all()
    assert frame.value.notna().all()
    normalized = frame.reported_value * frame.normalization_multiplier
    assert (frame.value - normalized).abs().le(1e-6).all()

    assert _value(frame, "total_fishery_economic_output") == (
        _value(frame, "fishery_output")
        + _value(frame, "fishery_industry_construction_output")
        + _value(frame, "fishery_circulation_services_output")
    )
    assert _value(frame, "total_aquatic_products") == (
        _value(frame, "aquaculture_production") + _value(frame, "capture_production")
    )
    assert _value(frame, "capture_production") == (
        _value(frame, "domestic_capture_production")
        + _value(frame, "distant_water_capture", "distant_water")
    )
    assert _value(frame, "total_aquatic_products") == (
        _value(frame, "marine_products", "marine")
        + _value(frame, "freshwater_products", "freshwater")
    )


def test_moa_2024_detailed_rounding_tolerances_are_explicitly_small():
    frame = pd.read_csv(PUBLIC / "moa_2024_detailed_fishery_statistics.csv")
    motor_tonnage = _value(frame, "vessel_tonnage", "motorized")
    component_tonnage = (
        _value(frame, "vessel_tonnage", "production")
        + _value(frame, "vessel_tonnage", "auxiliary")
    )
    assert abs(motor_tonnage - component_tonnage) <= 100.0

    processed_total = _value(frame, "processed_products")
    processed_components = (
        _value(frame, "processed_products", "marine")
        + _value(frame, "processed_products", "freshwater")
    )
    assert abs(processed_total - processed_components) <= 100.0

    trade_total = _value(frame, "trade_value")
    trade_components = (
        _value(frame, "trade_value", "export")
        + _value(frame, "trade_value", "import")
    )
    assert abs(trade_total - trade_components) <= 1.0


def test_environment_snapshot_retains_comparison_basis():
    frame = pd.read_csv(PUBLIC / "moa_fishery_environment_2024.csv")
    assert len(frame) == 12
    assert frame.data_label.eq("经过处理的数据（公开来源）").all()
    area = frame[frame.indicator == "monitored_water_area"].iloc[0]
    area_increase = frame[frame.indicator == "monitored_area_increase"].iloc[0]
    assert area.value == 10_160_000
    assert area_increase.value == 150_000
    assert area_increase.comparison_year == 2023


def test_latest_official_snapshot_reconciles_national_and_zhejiang_totals():
    frame = pd.read_csv(PUBLIC / "official_latest_aquatic_products_2025.csv")
    assert set(frame.geography_code) == {"CHN", "CN-ZJ"}
    assert frame.data_label.eq("经过处理的数据（公开来源）").all()

    national = frame[frame.geography_code == "CHN"].set_index("indicator").value
    assert national.total_aquatic_products == (
        national.aquaculture_production + national.capture_production
    )
    zhejiang = frame[frame.geography_code == "CN-ZJ"].set_index("indicator").value
    assert zhejiang.total_aquatic_products == (
        zhejiang.marine_products + zhejiang.freshwater_products
    )
