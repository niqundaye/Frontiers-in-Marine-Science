import json
import tomllib
from pathlib import Path

import yaml

from fishery_repro import __version__


ROOT = Path(__file__).resolve().parents[1]


def test_machine_readable_metadata_versions_are_synchronized():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    codemeta = json.loads((ROOT / "codemeta.json").read_text(encoding="utf-8"))
    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    version = project["project"]["version"]
    assert version == __version__ == citation["version"] == codemeta["version"] == zenodo["version"]


def test_reviewer_entry_points_and_availability_statements_exist():
    required = [
        "ARTIFACT_EVALUATION.md",
        "DATA_AVAILABILITY.md",
        "scripts/reviewer_quick_check.py",
        "Dockerfile",
        ".gitattributes",
    ]
    assert all((ROOT / path).is_file() for path in required)
    evaluation = (ROOT / "ARTIFACT_EVALUATION.md").read_text(encoding="utf-8")
    availability = (ROOT / "DATA_AVAILABILITY.md").read_text(encoding="utf-8")
    assert "Documentation" in evaluation
    assert "Completeness" in evaluation
    assert "Exercisability" in evaluation
    assert "not an author-run exact numerical replication" in availability
