# Artifact evaluation guide

## 1. Artifact identification

**Article:** Liu, N., Mao, N., and Huang, J. (2026), “Optimizing sustainable
fishery resource allocation in China: an improved adaptive NSGA-III approach
under multi-dimensional rigid constraints,” *Frontiers in Marine Science* 13,
1809036. <https://doi.org/10.3389/fmars.2026.1809036>

**Artifact version:** 0.3.0

**Repository:** <https://github.com/niqundaye/Frontiers-in-Marine-Science>

**License:** MIT for repository code; source-specific terms apply to data and
article-derived material.

This package supports independent inspection and execution of the disclosed
method, exact article-table transcription, manuscript-figure provenance,
processed-data replots, official-data checks, and a 248-variable executable
surrogate. It is **reviewer-ready**, but no official IEEE “Code Reviewed” badge
or exact author-run numerical replication is claimed.

## 2. Scope of the reproducibility claim

| Claim | Evidence | Reproducibility level |
|---|---|---|
| Article Tables 1–4 | `data/paper/`, `implementations/table_*` | Exact transcription and automated validation |
| Article Figures 1–10 | `data/processed/manuscript_figures/`, `results/figures/` | Direct DOCX panel extraction with SHA-256 provenance |
| Figure 2–10 numerical plotting inputs | `results/data/`, `implementations/figure_*` | Processed reconstruction from disclosed curves/anchors |
| 248-variable PPMS structure | `src/fishery_repro/model.py` | Executable structural reproduction |
| IA-NSGA-III operators and diagnostics | `src/fishery_repro/experiment.py`, `benchmark.py` | Executable implementation with fixed seeds and full logs |
| National public-data checks | `data/public/`, `src/fishery_repro/public_data.py` | Deterministic extraction with URL, date, unit conversion and source hash |
| Authors’ province-level coefficients and 30 original runs | Not published with the article | Not reproduced and never imputed as author data |

## 3. Reviewer prerequisites

- Python 3.12 recommended; Python 3.10 or later supported.
- Two CPU cores, 4 GB RAM and approximately 1 GB free disk space.
- No network connection is required for the quick reviewer check or checked-in
  result inspection.
- Network access is required only to refresh the public-source snapshots.
- The tracked artifact contains about 27 MiB across approximately 270 files.

Install:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pip install --no-deps -e .
```

Linux/macOS:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .
```

## 4. Evaluation tracks

### Track A — non-destructive reviewer check

Expected runtime: approximately 20–60 seconds on a modern laptop.

```powershell
.venv\Scripts\python scripts\reviewer_quick_check.py
```

This command:

1. verifies every tracked artifact against `ARTIFACT_MANIFEST.csv` (LF-canonical
   SHA-256 for text and raw-byte SHA-256 for binary files);
2. executes the package-level checks without rewriting repository files;
3. runs the complete unit-test suite;
4. runs the six-run CI smoke experiment in a temporary directory;
5. verifies run counts, generation counts, seven constraint columns and
   processed-surrogate disclosure;
6. prints a JSON report ending in `"status": "pass"`.

### Track B — checked-in demonstration reconstruction

Expected runtime: approximately 1–3 minutes. This path intentionally rewrites
generated result files.

```powershell
.venv\Scripts\python scripts\reproduce_research_artifact.py
```

Acceptance criteria:

- all tests pass;
- `results/PACKAGE_VALIDATION.csv` contains only `pass`;
- `results/experiments/processed_demo/run_summary.csv` has 15 runs;
- `generation_log.csv` has 450 generation records;
- final outputs expose 248 decision variables, three objectives and seven
  constraint residuals;
- `ARTIFACT_MANIFEST.csv` is regenerated.

### Track C — refresh public online data

This is intentionally separate from experiment reproduction so that temporary
network or source-site failures cannot invalidate the offline artifact.

```powershell
.venv\Scripts\python -m fishery_repro public-data
```

The refresh is fail-fast: required official statistics must be found by the
deterministic parser, and unavailable NBS province-level endpoint data are not
silently substituted.

### Track D — container execution

```bash
docker build -t fishery-artifact:0.3.0 .
docker run --rm fishery-artifact:0.3.0
```

The container entry point executes Track A. The same files can be imported into
Code Ocean or another container-based artifact platform.

## 5. IEEE-style evaluation criteria

### Documentation

- article and artifact are identified at the top of this guide;
- dependencies, installation, commands, expected runtimes and acceptance
  criteria are explicit;
- `DATA_AVAILABILITY.md` separates exact, processed, public and unavailable data;
- `docs/EXPERIMENT_PROTOCOL.md` specifies every experiment path.

### Completeness

- code, configurations, tests, processed inputs, checked-in outputs, provenance,
  environment files and checksums are included;
- every figure and table has a colocated implementation bundle;
- missing author material is explicitly listed rather than reconstructed without
  evidence.

### Exercisability

- `scripts/reviewer_quick_check.py` performs a non-destructive offline run;
- GitHub Actions repeats tests, smoke execution, package validation and artifact
  generation on Linux;
- the Dockerfile supplies a portable Python 3.12 execution environment.

## 6. Result locations

| Result | Location |
|---|---|
| Primary manuscript figures | `results/figures/` |
| Code-generated comparison figures | `results/processed_data_replots/` |
| Figure plotting data | `results/data/` |
| Demonstration experiment | `results/experiments/processed_demo/` |
| Per-result implementation bundles | `implementations/` |
| Official public datasets | `data/public/` |
| Package validation | `results/PACKAGE_VALIDATION.csv` |
| Whole-artifact hashes | `ARTIFACT_MANIFEST.csv` |

## 7. Archival requirement before journal submission

GitHub `main` is convenient but mutable. Before using the repository URL in a
final manuscript, create a versioned GitHub release and archive that release in
Zenodo or an equivalent repository. The included `.zenodo.json`,
`codemeta.json`, and `CITATION.cff` are prepared for version 0.3.0. Replace the
repository-only citation with the resulting persistent DOI in the final Data and
Code Availability Statement.
