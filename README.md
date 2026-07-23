# IA-NSGA-III Fishery Allocation Reproduction

[中文说明](README_zh.md)

This repository is a transparent, executable reconstruction of:

> Liu, N., Mao, N., & Huang, J. (2026). *Optimizing sustainable fishery resource allocation in China: an improved adaptive NSGA-III approach under multi-dimensional rigid constraints*. Frontiers in Marine Science, 13, 1809036. https://doi.org/10.3389/fmars.2026.1809036

It uses the figures embedded in the supplied manuscript for all 10 primary article figures, transcribes all 4 article tables, adds traceable public World Bank/FAO and Ministry data, and provides an executable 248-variable PPMS surrogate with chaotic initialization, constraint-feedback repair, and adaptive reference relocation.

## Reproduction status

This is **not an author-run exact replication**. As of 2026-07-23, the article page exposes no downloadable supplementary dataset or source-code archive. The 31-province coefficient matrix, regional TAC values, digitalization inputs, worker counts, prices/costs, and original 30-run optimization logs are not published. Derived and public-source material is consistently labelled as processed data:

| Level | Contents | Status |
|---|---|---|
| Exact transcription | Tables 1-4 and explicitly printed numeric anchors | Reproduced from the CC BY article |
| Processed data (public sources) | World Bank/FAO 2014-2023 series and accessible Ministry communiqués | Download script, source URL, retrieval date and license/terms notes included |
| Processed data (manuscript figures) | All 20 DOCX-embedded panels behind Figures 1-10 | Direct OOXML extraction, panel mapping, dimensions and SHA-256 included |
| Processed data (structured replots) | Figure 2-10 CSVs and code-generated comparison plots | Deterministic values anchored to disclosed curves and numeric values |
| Public-data surrogate | 248-variable PPMS optimization | Executable structural implementation; proxy regional coefficients |

Never cite the processed CSV files as the authors' original experimental logs.

## Quick start

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m fishery_repro all
.venv\Scripts\python -m fishery_repro public-data
.venv\Scripts\python -m pytest
```

Linux/macOS users can replace `.venv\Scripts\python` with `.venv/bin/python`.

## Outputs

`python -m fishery_repro all` creates:

- `results/figures/`: primary PNG Figures 1-10 composed from the supplied DOCX images;
- `results/processed_data_replots/`: code-generated PNG/SVG comparison plots;
- `results/data/`: the complete processed CSV used by the comparison plots for Figures 2-10;
- `results/tables/data_audit.csv`: table consistency and official-source checks;
- `results/benchmark/smoke_summary.csv`: a small executable surrogate benchmark;
- `results/MANIFEST.csv`: file sizes and SHA-256 checksums.

The default smoke benchmark is intentionally small. The paper setting (`N=200`, `Tmax=1000`, 30 independent runs) is recorded in `configs/paper.yaml`, but exact numerical comparison requires the unpublished author inputs.

## Repository map

```text
configs/             Paper and smoke-test settings
data/paper/          Exact table transcriptions
data/processed/      Extracted manuscript panels, mapping manifest, and processing notes
data/verified/       Official-source validation records
docs/                Data provenance, limitations, result map
scripts/             One-command runner and optional source downloader
src/fishery_repro/   Model, algorithms, figure generation, audit tooling
tests/               Data, model, and rendering tests
results/             Manuscript figures, processed-data replots, plot data, audits, benchmark summary
implementations/     Code + input data + output colocated for each figure/table
data/public/         Downloaded public data, source catalog, and workbook
```

## Licensing

Repository code is MIT licensed. Article-derived figures and table values are attributed to Liu et al. (2026) under the article's CC BY license. The China Fisheries Statistical Yearbooks are not redistributed; only article-transcribed values and limited official-communiqué values are included.
