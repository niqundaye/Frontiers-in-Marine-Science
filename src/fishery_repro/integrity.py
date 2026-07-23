from __future__ import annotations

import hashlib
from pathlib import Path


TEXT_SUFFIXES = {
    ".cff",
    ".csv",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".svg",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {".dockerignore", ".gitattributes", "Dockerfile", "LICENSE"}


def hash_mode(path: str | Path) -> str:
    target = Path(path)
    if target.suffix.lower() in TEXT_SUFFIXES or target.name in TEXT_FILENAMES:
        return "text_lf"
    return "binary"


def content_for_hash(path: str | Path, mode: str | None = None) -> bytes:
    target = Path(path)
    data = target.read_bytes()
    selected = mode or hash_mode(target)
    if selected == "text_lf":
        return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if selected == "binary":
        return data
    raise ValueError(f"Unsupported hash mode: {selected}")


def sha256_file(path: str | Path, mode: str | None = None) -> str:
    return hashlib.sha256(content_for_hash(path, mode)).hexdigest()
