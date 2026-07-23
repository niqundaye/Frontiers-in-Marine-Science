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
    assert {2015, 2016, 2019, 2020, 2021, 2022, 2023}.issubset(set(frame.year))
    assert frame.source_url.str.startswith("https://").all()
    assert frame.extraction_status.isin(["parsed", "not_found"]).all()
    assert (frame.extraction_status == "parsed").mean() >= 0.75


def test_catalog_marks_unavailable_province_data_without_imputation():
    catalog = source_catalog("2026-07-23")
    nbs = catalog[catalog.source_id == "nbs_a0407"].iloc[0]
    assert "403" in nbs.access
    assert not nbs.repository_file
