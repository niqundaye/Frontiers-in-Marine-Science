from __future__ import annotations

import csv
import hashlib
import io
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import ROOT


EXPECTED_SOURCE_SHA256 = "2ee3d23f1a5592b59e6c3e190bc361e1fdb4024405d7a8c5e2681fc3575bb2e0"
DATA_LABEL = "经过处理的数据"
DEFAULT_PANEL_DIR = ROOT / "data" / "processed" / "manuscript_figures" / "panels"
DEFAULT_MANIFEST = ROOT / "data" / "processed" / "manuscript_figures" / "manifest.csv"


@dataclass(frozen=True)
class PanelSpec:
    figure: int
    panel: str
    source_media: str
    width: int
    height: int
    caption: str

    @property
    def filename(self) -> str:
        suffix = self.panel if self.panel else ""
        return f"Figure_{self.figure:02d}{suffix}.png"


FIGURE_STEMS = {
    1: "Figure_01_PPMS_MOO_architecture",
    2: "Figure_02_convergence",
    3: "Figure_03_statistical_comparison",
    4: "Figure_04_kpi_radar",
    5: "Figure_05_pareto_sets",
    6: "Figure_06_parameter_sensitivity",
    7: "Figure_07_digitalization_sensitivity",
    8: "Figure_08_tac_sensitivity",
    9: "Figure_09_algorithm_ablation",
    10: "Figure_10_module_ablation",
}

PANELS = (
    PanelSpec(1, "", "image1.png", 1780, 1088, "PPMS-MOO architecture"),
    PanelSpec(2, "a", "image212.png", 1030, 790, "Hypervolume convergence"),
    PanelSpec(2, "b", "image213.png", 1014, 770, "IGD convergence"),
    PanelSpec(3, "a", "image214.png", 1294, 1332, "Hypervolume boxplot"),
    PanelSpec(3, "b", "image215.png", 1240, 1298, "IGD boxplot"),
    PanelSpec(4, "", "image216.png", 1528, 1322, "KPI radar comparison"),
    PanelSpec(5, "", "image217.png", 1564, 1296, "Three-dimensional Pareto sets"),
    PanelSpec(6, "a", "image218.png", 1316, 1232, "Adaptive adjustment factor sensitivity"),
    PanelSpec(6, "b", "image219.png", 1338, 1238, "Relocation frequency sensitivity"),
    PanelSpec(7, "a", "image222.png", 1372, 1324, "Social reliability sensitivity"),
    PanelSpec(7, "b", "image223.png", 1514, 1334, "Economic efficiency sensitivity"),
    PanelSpec(7, "c", "image224.png", 1512, 1336, "Ecological security sensitivity"),
    PanelSpec(8, "a", "image225.png", 1358, 1206, "Pareto fronts under TAC scenarios"),
    PanelSpec(8, "b", "image226.png", 1304, 1172, "Hypervolume under TAC scenarios"),
    PanelSpec(9, "a", "image227.png", 1516, 1328, "Algorithm ablation: social reliability"),
    PanelSpec(9, "b", "image228.png", 1482, 1340, "Algorithm ablation: economic efficiency"),
    PanelSpec(9, "c", "image229.png", 1500, 1342, "Algorithm ablation: ecological security"),
    PanelSpec(10, "a", "image230.png", 1474, 1264, "Module ablation: social reliability"),
    PanelSpec(10, "b", "image231.png", 1478, 1272, "Module ablation: economic efficiency"),
    PanelSpec(10, "c", "image232.png", 1486, 1288, "Module ablation: ecological security"),
)


def _sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def import_panels_from_docx(
    docx_path: str | Path,
    panel_dir: str | Path = DEFAULT_PANEL_DIR,
    manifest_path: str | Path = DEFAULT_MANIFEST,
) -> list[Path]:
    """Extract the manuscript's embedded figure panels without redrawing them."""

    source = Path(docx_path)
    destination = Path(panel_dir)
    manifest = Path(manifest_path)
    destination.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    source_hash = _sha256_file(source)
    written: list[Path] = []
    rows: list[dict[str, str | int]] = []

    with zipfile.ZipFile(source) as archive:
        for spec in PANELS:
            archive_name = f"word/media/{spec.source_media}"
            blob = archive.read(archive_name)
            with Image.open(io.BytesIO(blob)) as image:
                actual_size = image.size
            expected_size = (spec.width, spec.height)
            if actual_size != expected_size:
                raise ValueError(
                    f"unexpected size for {archive_name}: {actual_size}; expected {expected_size}"
                )
            output = destination / spec.filename
            output.write_bytes(blob)
            written.append(output)
            rows.append(
                {
                    "figure": spec.figure,
                    "panel": spec.panel or "single",
                    "caption": spec.caption,
                    "source_document": source.name,
                    "source_document_sha256": source_hash,
                    "source_media_part": archive_name,
                    "processed_file": output.relative_to(ROOT).as_posix(),
                    "pixel_width": spec.width,
                    "pixel_height": spec.height,
                    "processed_file_sha256": _sha256_bytes(blob),
                    "data_label": DATA_LABEL,
                    "processing": "direct OOXML media extraction; pixels unchanged",
                }
            )

    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return written


def _label_panel(image: Image.Image, panel: str) -> Image.Image:
    label_height = 54
    labelled = Image.new("RGB", (image.width, image.height + label_height), "white")
    labelled.paste(image.convert("RGB"), (0, label_height))
    draw = ImageDraw.Draw(labelled)
    font = ImageFont.load_default(size=34)
    draw.text((12, 7), f"({panel})", fill="black", font=font)
    return labelled


def _row(images: list[Image.Image], gap: int = 36) -> Image.Image:
    width = sum(image.width for image in images) + gap * (len(images) - 1)
    height = max(image.height for image in images)
    canvas = Image.new("RGB", (width, height), "white")
    x = 0
    for image in images:
        y = (height - image.height) // 2
        canvas.paste(image, (x, y))
        x += image.width + gap
    return canvas


def _with_margin(image: Image.Image, margin: int = 30) -> Image.Image:
    canvas = Image.new("RGB", (image.width + 2 * margin, image.height + 2 * margin), "white")
    canvas.paste(image, (margin, margin))
    return canvas


def _compose_figure(specs: list[PanelSpec], panel_dir: Path) -> Image.Image:
    loaded = [Image.open(panel_dir / spec.filename).convert("RGB") for spec in specs]
    if len(specs) == 1:
        return loaded[0]
    labelled = [_label_panel(image, spec.panel) for image, spec in zip(loaded, specs, strict=True)]
    if len(labelled) == 2:
        return _with_margin(_row(labelled))

    top = _row(labelled[:2])
    bottom = labelled[2]
    gap = 42
    width = max(top.width, bottom.width)
    canvas = Image.new("RGB", (width, top.height + gap + bottom.height), "white")
    canvas.paste(top, ((width - top.width) // 2, 0))
    canvas.paste(bottom, ((width - bottom.width) // 2, top.height + gap))
    return _with_margin(canvas)


def compose_manuscript_figures(
    panel_dir: str | Path = DEFAULT_PANEL_DIR,
    output_dir: str | Path = ROOT / "results" / "figures",
) -> list[Path]:
    """Compose Figure 1-10 PNGs from the extracted manuscript panels."""

    source = Path(panel_dir)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for figure, stem in FIGURE_STEMS.items():
        specs = [spec for spec in PANELS if spec.figure == figure]
        if len(specs) == 1:
            output = destination / f"{stem}.png"
            shutil.copy2(source / specs[0].filename, output)
        else:
            composite = _compose_figure(specs, source)
            output = destination / f"{stem}.png"
            composite.save(output, format="PNG", optimize=True, dpi=(300, 300))
        paths.append(output)
    return paths


def source_matches_recorded_manuscript(docx_path: str | Path) -> bool:
    return _sha256_file(Path(docx_path)) == EXPECTED_SOURCE_SHA256
