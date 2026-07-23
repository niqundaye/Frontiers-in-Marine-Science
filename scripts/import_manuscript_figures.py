from __future__ import annotations

import argparse
from pathlib import Path

from fishery_repro.manuscript_figures import (
    EXPECTED_SOURCE_SHA256,
    compose_manuscript_figures,
    import_panels_from_docx,
    source_matches_recorded_manuscript,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract the exact embedded figure panels from 316Manuscript.DOCX and compose Figures 1-10."
    )
    parser.add_argument("docx", type=Path, help="Path to 316Manuscript.DOCX")
    args = parser.parse_args()

    if not source_matches_recorded_manuscript(args.docx):
        raise SystemExit(
            "The DOCX hash differs from the recorded source. "
            f"Expected SHA-256 {EXPECTED_SOURCE_SHA256}; review the figure mapping before importing."
        )
    panels = import_panels_from_docx(args.docx)
    figures = compose_manuscript_figures()
    print(f"Imported {len(panels)} manuscript panels.")
    print(f"Composed {len(figures)} primary result figures.")


if __name__ == "__main__":
    main()
