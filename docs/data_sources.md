# Data sources and provenance

## Primary article

- Article landing page: https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2026.1809036/full
- DOI: https://doi.org/10.3389/fmars.2026.1809036
- Local PDF audited during reconstruction: SHA-256 `14790dc6b70f6b7952c74034e85ed15b6be3f719830adf026d4d1e9ea3644e1a`

The article is CC BY. Tables 1-4 in `data/paper/` were transcribed from the PDF and checked against the HTML rendering.

## Manuscript figure source

- User-supplied source: `316Manuscript.DOCX`
- SHA-256: `2ee3d23f1a5592b59e6c3e190bc361e1fdb4024405d7a8c5e2681fc3575bb2e0`
- Mapping: 20 embedded PNG panels mapped to Figures 1-10 in `data/processed/manuscript_figures/manifest.csv`
- Label: `经过处理的数据`

The primary PNGs in `results/figures/` use these DOCX panels. Multi-panel figures receive only white-background layout and `(a)/(b)/(c)` labels. Code-generated comparison plots are kept separately in `results/processed_data_replots/`.

## Official checks

- 2023 national fishery economic statistics communiqué: https://yyj.moa.gov.cn/gzdt/202407/t20240705_6458486.htm
- 2022 national fishery economic statistics communiqué: https://yyj.moa.gov.cn/yqxx/202306/t20230628_6431131.htm
- 2021 national fishery economic statistics communiqué: https://yyj.moa.gov.cn/gzdt/202207/t20220721_6405222.htm
- Ministry fishery-information index: https://yyj.moa.gov.cn/yqxx/

The 2023 communiqué confirms, after normal rounding, total output, marine aquaculture, domestic marine capture, distant-water capture, processing-enterprise count, cold-storage count, fleet power, fisher income, and export value.

## Open online datasets added to the repository

- World Bank Indicators API, with FAO as the underlying source: `ER.FSH.PROD.MT`, `ER.FSH.AQUA.MT`, and `ER.FSH.CAPT.MT`, China, 2014-2023. The API snapshot and CC BY 4.0 license link are recorded row by row in `data/public/world_bank_fao_china_fisheries_2014_2023.csv`.
- Accessible Ministry annual communiqués for 2015, 2016, and 2019-2023 are parsed into long-form records in `data/public/moa_national_fishery_statistics.csv`. Missing fields remain `not_found`; they are never interpolated.
- National Bureau of Statistics provincial indicator `A0407` is documented in `data/public/source_catalog.csv`. The official automated endpoint returned HTTP 403 during this retrieval, so the repository does not redistribute values from paywalled third-party aggregators.

World Bank/FAO totals and Ministry totals are definitionally different and should be treated as separate series rather than forced to match.

## China Fisheries Statistical Yearbook

The article cites the 2014-2023 yearbooks. Those volumes are commercial/copyrighted publications and are not copied into this repository. Users with lawful access should build a province-year input table with these minimum fields:

`province, year, marine_capture, freshwater_capture, marine_aquaculture, freshwater_aquaculture, processed_volume, cold_storage_throughput, fleet_power, fisher_workforce, fisher_income, export_value, circulation_value, digital_infrastructure, traceability_adoption, temperature_monitoring_coverage, TAC`

The public surrogate in `src/fishery_repro/model.py` makes every missing coefficient deterministic and replaceable.
