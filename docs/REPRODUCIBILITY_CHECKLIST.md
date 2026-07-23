# Reproducibility checklist

The primary reviewer entry point is `ARTIFACT_EVALUATION.md`. The checklist below
maps repository evidence to the documentation, completeness and exercisability
criteria used by computational-artifact reviewers.

| Item | Repository evidence |
|---|---|
| Artifact identification and scope | `README.md`, `ARTIFACT_EVALUATION.md` |
| Data and code availability statement | `DATA_AVAILABILITY.md` |
| Fixed software environment | pinned `requirements.txt`, `requirements-dev.txt`, `environment.yml` |
| Containerized environment | `Dockerfile`, `.dockerignore` |
| Complete experimental parameters | `configs/experiments/*.yaml` |
| Random seeds | explicit `seeds` list and per-run seed in every output row |
| Independent repeats | `run_id` and `seed` in `run_summary.csv` |
| Per-generation trace | `generation_log.csv` |
| Adaptive-state trace | `reference_relocation_log.csv` |
| Final objectives and constraints | `final_population_objectives_constraints.csv` |
| Full 248-dimensional solutions | `final_population_decision_vectors.csv` |
| Run metadata | `run_metadata.json` with config hash and package versions |
| Raw/processed distinction | `data_status` in configs and generated CSV/JSON |
| Per-figure code and input | `implementations/figure_01` through `figure_10` |
| Per-figure derived result | `derived_data.csv` |
| Per-figure integrity audit | `validation_report.json` with input SHA-256 |
| Exact article-table transcription | `data/paper/` and `implementations/table_*` |
| Public-source provenance | `data/public/source_catalog.csv` |
| Manuscript image provenance | `data/processed/manuscript_figures/manifest.csv` |
| Automated tests | `tests/` and `.github/workflows/reproduce.yml` |
| Whole-package validation | `scripts/validate_reproducibility_package.py` |
| Non-destructive reviewer execution | `scripts/reviewer_quick_check.py` |
| Whole-artifact checksums | `ARTIFACT_MANIFEST.csv` |
| Machine-readable citation metadata | `CITATION.cff`, `codemeta.json`, `.zenodo.json` |
| Cross-platform line-ending policy | `.gitattributes` |
| Known missing author material | README limitations and experiment metadata disclosure |

## Acceptance criteria

- `python scripts/reviewer_quick_check.py` finishes with `"status": "pass"`.
- The package validator reports no failed checks.
- The unit-test suite reports no failures.
- The smoke experiment contains every declared algorithm–seed pair and generation.
- Every detailed public-data row retains a source URL, retrieval date and source hash.
- No unavailable author input is labelled as raw or original author data.
