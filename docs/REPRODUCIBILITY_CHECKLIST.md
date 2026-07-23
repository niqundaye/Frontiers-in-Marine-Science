# Reproducibility checklist

| Item | Repository evidence |
|---|---|
| Fixed software environment | pinned `requirements.txt`, `requirements-dev.txt`, `environment.yml` |
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
| Whole-artifact checksums | `ARTIFACT_MANIFEST.csv` |
| Known missing author material | README limitations and experiment metadata disclosure |
