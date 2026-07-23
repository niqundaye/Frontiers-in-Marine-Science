# IA-NSGA-III Fishery Allocation — Reproducibility Artifact

[![Reproduce](https://github.com/niqundaye/Frontiers-in-Marine-Science/actions/workflows/reproduce.yml/badge.svg)](https://github.com/niqundaye/Frontiers-in-Marine-Science/actions/workflows/reproduce.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/Code%20license-MIT-green.svg)](LICENSE)

[中文说明](README_zh.md) · [Artifact evaluation guide](ARTIFACT_EVALUATION.md) ·
[Data and code availability](DATA_AVAILABILITY.md) ·
[Experiment protocol](docs/EXPERIMENT_PROTOCOL.md)

## Artifact identification

This repository accompanies:

> Liu, N., Mao, N., and Huang, J. (2026). “Optimizing sustainable fishery
> resource allocation in China: an improved adaptive NSGA-III approach under
> multi-dimensional rigid constraints.” *Frontiers in Marine Science*, 13,
> 1809036. <https://doi.org/10.3389/fmars.2026.1809036>

Artifact version **0.3.0** provides code, configurations, processed data,
official-source data, checked-in outputs, tests, environment definitions,
provenance records and machine-readable validation for independent review.

> **Reproducibility boundary:** this is a transparent reconstruction and
> executable public-data surrogate, not an author-run exact numerical
> replication. The article does not publish the complete 31-province coefficient
> matrix, regional TAC values, digitalization inputs, income/cost coefficients or
> the original 30-run logs. The repository does not invent those materials.

## Reviewer quick check

Python 3.12 is recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pip install --no-deps -e .
.venv\Scripts\python scripts\reviewer_quick_check.py
```

Linux/macOS:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python scripts/reviewer_quick_check.py
```

The reviewer command is offline and non-destructive. It verifies the canonical
SHA-256 manifest (LF-normalized text, raw binary), executes the package checks and
unit tests, runs the six-run smoke experiment in a temporary directory, validates
its dimensions and prints a JSON report ending in `"status": "pass"`.

## Reproducibility claims

| Component | Evidence | Status |
|---|---|---|
| Tables 1–4 | `data/paper/`, `implementations/table_*` | Exact transcription and automated validation |
| Figures 1–10 | `data/processed/manuscript_figures/`, `results/figures/` | Direct DOCX extraction with panel mapping and SHA-256 |
| Figure 2–10 plotting values | `results/data/`, `implementations/figure_*` | Processed reconstruction from disclosed curves and anchors |
| 248-variable PPMS model | `src/fishery_repro/model.py` | Executable structural reproduction |
| IA-NSGA-III, NSGA-III and NSGA-II runs | `src/fishery_repro/experiment.py` | Fixed seeds, explicit operators, per-generation logs and final solutions |
| National public-data checks | `data/public/`, `src/fishery_repro/public_data.py` | Deterministic extraction with units, URLs, dates and source hashes |
| Authors’ private inputs and original logs | Not published | Explicitly unavailable; not imputed as author data |

All reconstructed or newly generated records are labelled **processed data** or
**public-data surrogate**. Do not cite `results/data/` or
`results/experiments/processed_demo/` as the authors’ original run logs.

## Evaluation paths

| Path | Command | Network | Typical purpose |
|---|---|---:|---|
| Reviewer check | `python scripts/reviewer_quick_check.py` | No | Integrity, tests and smoke execution |
| Full checked-in demonstration | `python scripts/reproduce_research_artifact.py` | No | Rebuild figures, surrogate experiment and audits |
| Public-data refresh | `python -m fishery_repro public-data` | Yes | Refresh official online snapshots |
| Container | `docker build -t fishery-artifact:0.3.0 .` then `docker run --rm fishery-artifact:0.3.0` | Build only | Portable reviewer check |

The paper-scale protocol (`population=200`, `generations=1000`, 30 repeats per
algorithm) is recorded in `configs/experiments/paper_protocol.yaml`. It is a
protocol declaration, not evidence that unpublished author inputs were recovered.

## Checked-in evidence

- 10 primary manuscript figures and 10 code-generated comparison figures;
- 4 exact article-table transcriptions;
- 15 demonstration runs and 450 generation records;
- 720 final-population solutions with three objectives and seven constraints;
- complete 248-dimensional decision vectors;
- 99 detailed 2024 Ministry fishery records;
- 12 official 2024 fishery-environment records;
- 6 latest 2025 national/Zhejiang aquatic-product records;
- package validation report and whole-artifact SHA-256 manifest.

## Repository structure

```text
ARTIFACT_EVALUATION.md   Reviewer protocol, runtimes and acceptance criteria
DATA_AVAILABILITY.md     Submission-ready data/code availability and restrictions
configs/                 Paper, demonstration and CI experiment configurations
data/paper/              Exact article-table transcriptions
data/processed/          DOCX-extracted figure panels and provenance
data/public/             Official public data, source catalog and review workbook
data/verified/           Independent official-value checks
docs/                    Algorithms, experiment protocol, provenance and limitations
implementations/         Colocated code, input, output and validation for each result
results/                 Checked-in figures, data, experiments and validation reports
scripts/                 Reviewer check, full runner, download and audit tools
src/fishery_repro/       Model, algorithms, data and result pipelines
tests/                   Data, model, metadata, rendering and integration tests
```

## Data, code and archival metadata

`DATA_AVAILABILITY.md` contains the recommended manuscript statements and
source-specific restrictions. `CITATION.cff`, `codemeta.json` and `.zenodo.json`
describe artifact version 0.3.0.

GitHub `main` is mutable. Before final submission, create a versioned GitHub
release, archive it in Zenodo or an equivalent repository, and place the resulting
persistent DOI in the manuscript.

## License

Repository code is MIT licensed. Article-derived material requires attribution
under the article’s CC BY terms. Public datasets retain their source-specific
terms. China Fisheries Statistical Yearbooks are not redistributed.
