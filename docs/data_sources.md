# Data sources and provenance

## Primary article

- Article landing page: https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2026.1809036/full
- DOI: https://doi.org/10.3389/fmars.2026.1809036
- Local PDF audited during reconstruction: SHA-256 `14790dc6b70f6b7952c74034e85ed15b6be3f719830adf026d4d1e9ea3644e1a`

The article is CC BY. Tables 1-4 in `data/paper/` were transcribed from the PDF and checked against the HTML rendering.

## Official checks

- 2023 national fishery economic statistics communiqué: https://yyj.moa.gov.cn/gzdt/202407/t20240705_6458486.htm
- 2022 national fishery economic statistics communiqué: https://yyj.moa.gov.cn/yqxx/202306/t20230628_6431131.htm
- 2021 national fishery economic statistics communiqué: https://yyj.moa.gov.cn/gzdt/202207/t20220721_6405222.htm
- Ministry fishery-information index: https://yyj.moa.gov.cn/yqxx/

The 2023 communiqué confirms, after normal rounding, total output, marine aquaculture, domestic marine capture, distant-water capture, processing-enterprise count, cold-storage count, fleet power, fisher income, and export value.

## China Fisheries Statistical Yearbook

The article cites the 2014-2023 yearbooks. Those volumes are commercial/copyrighted publications and are not copied into this repository. Users with lawful access should build a province-year input table with these minimum fields:

`province, year, marine_capture, freshwater_capture, marine_aquaculture, freshwater_aquaculture, processed_volume, cold_storage_throughput, fleet_power, fisher_workforce, fisher_income, export_value, circulation_value, digital_infrastructure, traceability_adoption, temperature_monitoring_coverage, TAC`

The public surrogate in `src/fishery_repro/model.py` makes every missing coefficient deterministic and replaceable.

