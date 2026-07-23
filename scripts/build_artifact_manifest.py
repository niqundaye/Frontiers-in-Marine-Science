from __future__ import annotations

from pathlib import Path

import pandas as pd

from fishery_repro.integrity import content_for_hash, hash_mode, sha256_file


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "ARTIFACT_MANIFEST.csv"
INCLUDED_ROOTS = (
    ".github",
    "configs",
    "data",
    "docs",
    "implementations",
    "results",
    "scripts",
    "src",
    "tests",
)
INCLUDED_FILES = (
    ".dockerignore",
    ".gitattributes",
    ".zenodo.json",
    "ARTIFACT_EVALUATION.md",
    "CITATION.cff",
    "DATA_AVAILABILITY.md",
    "Dockerfile",
    "LICENSE",
    "README.md",
    "README_zh.md",
    "codemeta.json",
    "environment.yml",
    "pyproject.toml",
    "requirements-dev.txt",
    "requirements.txt",
)


def provenance_class(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    if relative.startswith("data/paper/"):
        return "exact_article_transcription"
    if relative.startswith("data/public/") or relative.startswith("data/verified/"):
        return "public_source"
    if relative.startswith("data/processed/") or relative.startswith("results/"):
        return "processed_data"
    if relative.startswith("implementations/"):
        return "per_result_artifact"
    if path.suffix.lower() in {".py", ".mjs", ".js", ".yml", ".yaml", ".toml"}:
        return "code_or_configuration"
    return "documentation_or_license"


def main() -> None:
    paths: list[Path] = [ROOT / name for name in INCLUDED_FILES]
    for root_name in INCLUDED_ROOTS:
        paths.extend(
            path
            for path in (ROOT / root_name).rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix.lower() not in {".pyc", ".pyo"}
            and not path.name.endswith(".inspect.ndjson")
        )
    unique = sorted({path.resolve() for path in paths if path.exists() and path.resolve() != TARGET.resolve()})
    rows = []
    for path in unique:
        mode = hash_mode(path)
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": len(content_for_hash(path, mode)),
                "sha256": sha256_file(path, mode),
                "hash_mode": mode,
                "provenance_class": provenance_class(path),
            }
        )
    pd.DataFrame(rows).to_csv(TARGET, index=False, lineterminator="\n")
    print(f"{len(rows)} files recorded")
    print(TARGET.resolve())


if __name__ == "__main__":
    main()
