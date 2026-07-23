from __future__ import annotations

import hashlib

import pandas as pd
from PIL import Image

from fishery_repro.config import ROOT
from fishery_repro.manuscript_figures import DATA_LABEL, FIGURE_STEMS, PANELS


PROCESSED = ROOT / "data" / "processed" / "manuscript_figures"


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_all_docx_panels_have_auditable_manifest_rows():
    manifest = pd.read_csv(PROCESSED / "manifest.csv")
    assert len(manifest) == 20
    assert manifest.data_label.eq(DATA_LABEL).all()
    assert manifest.source_document_sha256.nunique() == 1
    assert manifest.source_document_sha256.iloc[0] == (
        "2ee3d23f1a5592b59e6c3e190bc361e1fdb4024405d7a8c5e2681fc3575bb2e0"
    )
    for row in manifest.itertuples(index=False):
        path = ROOT / row.processed_file
        assert path.is_file()
        assert _sha256(path) == row.processed_file_sha256
        with Image.open(path) as image:
            assert image.size == (row.pixel_width, row.pixel_height)


def test_primary_results_are_manuscript_pngs_and_code_replots_are_separate():
    assert len(PANELS) == 20
    for stem in FIGURE_STEMS.values():
        primary = ROOT / "results" / "figures" / f"{stem}.png"
        replot_png = ROOT / "results" / "processed_data_replots" / f"{stem}.png"
        replot_svg = ROOT / "results" / "processed_data_replots" / f"{stem}.svg"
        assert primary.is_file()
        assert replot_png.is_file()
        assert replot_svg.is_file()
        assert _sha256(primary) != _sha256(replot_png)


def test_primary_result_directory_does_not_mislabel_replots_as_source_svg():
    primary_dir = ROOT / "results" / "figures"
    assert len(list(primary_dir.glob("*.png"))) == 10
    assert not list(primary_dir.glob("*.svg"))
