# Data dictionary

All files below retain a provenance class. “经过处理的数据” never means author
raw data.

## Experiment outputs

### `generation_log.csv`

| Field | Meaning |
|---|---|
| `algorithm`, `run_id`, `seed`, `generation` | independent-run identity |
| `evaluations`, `population_size` | algorithm state |
| `feasible_count`, `feasible_fraction` | constraint feasibility |
| `mean_total_constraint_violation`, `max_total_constraint_violation` | sum of positive residuals |
| `non_dominated_count` | non-dominated members of the active comparison population |
| `hv_against_zero_reference` | minimization-space HV using `(0,0,0)` as reference |
| `max_*` | maximum social, economic and ecological score in the selected population |

### `reference_relocation_log.csv`

`generation` identifies each adaptive update; `mean_direction_shift` is the mean
Euclidean distance between old and relocated reference directions.

### `final_population_objectives_constraints.csv`

The file contains solution identity, feasibility, decoded national quantities,
`social_reliability`, `economic_efficiency`, `ecological_security`, and residuals
`g_*` for all seven constraints. Residuals are feasible at or below zero.

### `final_population_decision_vectors.csv`

Columns use `x_rRR_sS_mM`: one-based region (`RR=01..31`), sector (`S=1..4`) and
mode (`M=1..2`). Values are normalized to `[0,1]`; `model.decode` converts them to
tonnes.

### `run_summary.csv` and `algorithm_summary.csv`

Run-level HV uses reference point `(1.05,1.05,1.05)` after converting maximization
scores to costs `1-F`. IGD is measured against the pooled non-dominated front created
from the current experiment and therefore cannot be interpreted as the authors'
unpublished reference front.

## Figure input files

The executable schema for every `results/data/figure_*.csv` is in
`src/fishery_repro/result_pipeline.py`. Each corresponding
`implementations/figure_*/validation_report.json` stores the input SHA-256, row count,
column list and semantic checks. Each `derived_data.csv` records the actual
transformation result used for review.

## Article and public data

- `data/paper/`: exact transcriptions of article Tables 1–4.
- `data/processed/manuscript_figures/`: DOCX-extracted figure panels and hash manifest.
- `data/public/`: downloaded public series and retrieval catalog. Detailed official
  extracts preserve `reported_value`, `reported_unit`, the numeric
  `normalization_multiplier`, normalized `value`/`unit`, official `source_url`,
  retrieval date, source-page SHA-256 and the label `经过处理的数据（公开来源）`.
- `data/verified/`: limited official national values used for independent checks.

### Detailed public-data tables

- `moa_2024_detailed_fishery_statistics.csv`: one observation per
  indicator/category. `yoy_pct` is signed (declines are negative) and
  `share_pct` is populated only where the official table reports a share.
- `moa_fishery_environment_2024.csv`: `comparison_year` and
  `change_direction` distinguish current levels from reported changes. Percentage
  rows are decline magnitudes, not absolute pollutant concentrations.
- `official_latest_aquatic_products_2025.csv`: `category_basis` prevents the
  national production-method split (aquaculture/capture) from being confused with
  Zhejiang's water-body split (marine/freshwater).
