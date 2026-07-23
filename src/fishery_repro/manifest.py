from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from .config import ROOT


def write_manifest(root: str | Path | None = None, output: str | Path | None = None) -> Path:
    base = (Path(root) if root else ROOT / "results").resolve()
    target = (Path(output) if output else base / "MANIFEST.csv").resolve()
    rows: list[dict[str, object]] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.resolve() == target.resolve():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        try:
            display_path = path.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            display_path = path.resolve().relative_to(base).as_posix()
        rows.append({"path": display_path, "bytes": path.stat().st_size, "sha256": digest})
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(target, index=False)
    return target
