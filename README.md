# IA-NSGA-III Fishery Allocation Reproduction

[中文说明](README_zh.md)

This repository is a transparent, executable reconstruction of:

> Liu, N., Mao, N., & Huang, J. (2026). *Optimizing sustainable fishery resource allocation in China: an improved adaptive NSGA-III approach under multi-dimensional rigid constraints*. Frontiers in Marine Science, 13, 1809036. https://doi.org/10.3389/fmars.2026.1809036

It reproduces all 10 article figures, transcribes all 4 article tables, validates disclosed 2023 statistics against the official Ministry of Agriculture and Rural Affairs communiqué, and provides an executable 248-variable PPMS surrogate with chaotic initialization, constraint-feedback repair, and adaptive reference relocation.

## Reproduction status

This is **not an author-run exact replication**. As of 2026-07-23, the article page exposes no downloadable supplementary dataset or source-code archive. The 31-province coefficient matrix, regional TAC values, digitalization inputs, worker counts, prices/costs, and original 30-run optimization logs are not published. The repository therefore distinguishes three evidence levels:

| Level | Contents | Status |
|---|---|---|
| Exact transcription | Tables 1-4 and explicitly printed numeric anchors | Reproduced from the CC BY article |
| Official validation | 2023 national statistics | Cross-checked against the official communiqué; 2021-2022 official links are also documented |
| Calibrated reconstruction | Figures 2-10 and undisclosed plot points | Deterministic curves/data anchored to reported values |
| Public-data surrogate | 248-variable PPMS optimization | Executable structural implementation; proxy regional coefficients |

Never cite the calibrated CSV files as the authors' original experimental logs.

## Quick start

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m fishery_repro all
.venv\Scripts\python -m pytest
```

Linux/macOS users can replace `.venv\Scripts\python` with `.venv/bin/python`.

## Outputs

`python -m fishery_repro all` creates:

- `results/figures/`: Figures 1-10 in PNG and SVG;
- `results/data/`: the complete plot-ready CSV behind Figures 2-10;
- `results/tables/data_audit.csv`: table consistency and official-source checks;
- `results/benchmark/smoke_summary.csv`: a small executable surrogate benchmark;
- `results/MANIFEST.csv`: file sizes and SHA-256 checksums.

The default smoke benchmark is intentionally small. The paper setting (`N=200`, `Tmax=1000`, 30 independent runs) is recorded in `configs/paper.yaml`, but exact numerical comparison requires the unpublished author inputs.

## Repository map

```text
configs/             Paper and smoke-test settings
data/paper/          Exact table transcriptions
data/verified/       Official-source validation records
docs/                Data provenance, limitations, result map
scripts/             One-command runner and optional source downloader
src/fishery_repro/   Model, algorithms, figure generation, audit tooling
tests/               Data, model, and rendering tests
results/             Generated figures, plot data, audits, benchmark summary
```

## Licensing

Repository code is MIT licensed. Article-derived table values and the conceptual recreation of Figure 1 are attributed to Liu et al. (2026) under the article's CC BY license. The China Fisheries Statistical Yearbooks are not redistributed; only article-transcribed values and limited official-communiqué validation values are included.
