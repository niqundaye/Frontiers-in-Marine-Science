# Data and code availability

## Recommended manuscript statement

The code, configurations, processed figure data, article-table transcriptions,
official public-data extracts, provenance records and executable surrogate
experiments supporting this reconstruction are available at
<https://github.com/niqundaye/Frontiers-in-Marine-Science>. A versioned archival
DOI should replace or accompany this mutable repository URL before final journal
submission.

Publicly available datasets analyzed in this work are identified row by row in
`data/public/source_catalog.csv`. Each detailed official extract retains the
reported value and unit, normalization multiplier, normalized value, source URL,
retrieval date and source-page SHA-256.

This package is **not an author-run exact numerical replication**. The published
article does not expose the complete 31-province coefficient matrix, regional
TAC values, digitalization-index inputs, income/cost coefficients or the authors’
30 original optimization logs. These materials are neither fabricated nor
presented as public data. The executable experiment is explicitly labelled a
processed public-data surrogate.

## Data classification

| Class | Repository location | Meaning |
|---|---|---|
| Exact article transcription | `data/paper/` | Values printed in article Tables 1–4 |
| Manuscript figure source | `data/processed/manuscript_figures/` | Panels directly extracted from the supplied DOCX with hashes |
| Processed plotting data | `results/data/` | Reconstructed values used for code-generated comparison plots |
| Official public data | `data/public/` | World Bank/FAO, Ministry and statistical-bureau data with provenance |
| Limited independent checks | `data/verified/` | Official national values used for cross-checking |
| Public-data surrogate outputs | `results/experiments/processed_demo/` | New executable runs, not author-run logs |
| Unavailable author inputs | Not in repository | Province-level coefficients and original run logs not published |

## Public sources

- World Bank Indicators API with FAO as the underlying source:
  `ER.FSH.PROD.MT`, `ER.FSH.AQUA.MT`, and `ER.FSH.CAPT.MT`.
- Ministry of Agriculture and Rural Affairs annual fishery economic
  communiqués, including the detailed 2024 communiqué.
- Joint Ministry fishery ecological-environment communiqué summary for 2024.
- National Bureau of Statistics 2025 national communiqué.
- Zhejiang Provincial Bureau of Statistics 2025 communiqué.

Exact URLs, retrieval status, terms notes and repository mappings are maintained
in `data/public/source_catalog.csv`.

## Restrictions and non-redistributed sources

- China Fisheries Statistical Yearbook volumes are not redistributed because
  they are commercial/copyrighted publications.
- The NBS province-level A0407 endpoint returned HTTP 403 during automated
  retrieval. No third-party or paywalled replacement values are presented as
  official NBS downloads.
- Article-derived images and table values remain subject to the article’s CC BY
  terms and attribution requirements.

## Code availability

- Source package: `src/fishery_repro/`
- Experiment configurations: `configs/experiments/`
- One-command reviewer check: `scripts/reviewer_quick_check.py`
- Full demonstration runner: `scripts/reproduce_research_artifact.py`
- Automated tests: `tests/`
- Continuous integration: `.github/workflows/reproduce.yml`
- Environment definitions: `requirements*.txt`, `environment.yml`, `Dockerfile`

Repository code is licensed under MIT. Machine-readable citation and archival
metadata are provided in `CITATION.cff`, `codemeta.json`, and `.zenodo.json`.
