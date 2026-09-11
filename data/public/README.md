# Public online data

This directory contains openly retrievable data added after the article reconstruction.

| File | Contents | Evidence level |
|---|---|---|
| `world_bank_fao_china_fisheries_2014_2023.csv` | China total, aquaculture and capture production from FAO via the World Bank API | 经过处理的数据（公开来源），CC BY 4.0 |
| `moa_national_fishery_statistics.csv` | Key values parsed from accessible Ministry annual communiqués, now including 2024 | 经过处理的数据（官方公报） |
| `moa_2024_detailed_fishery_statistics.csv` | 99 long-form records covering economic output, production by species/water body, aquaculture area, fleet, population, processing, trade and disasters | 经过处理的数据（公开来源）；reported and normalized values are both retained |
| `moa_fishery_environment_2024.csv` | 12 monitoring-network and exceedance-area change indicators from the joint ecological-environment communique | 经过处理的数据（公开来源）；change magnitudes are not concentration levels |
| `official_latest_aquatic_products_2025.csv` | 2025 national total/aquaculture/capture and Zhejiang total/marine/freshwater production | 经过处理的数据（公开来源）；category bases are explicitly separated |
| `nbs_2024_31_province_public_panel.csv` | 31-province 2024 production, population, income, wastewater, freight and enterprise e-commerce observations from six NBS yearbook tables | 官方公开数据转录；不是作者历史输入 |
| `nbs_2024_31_province_public_panel_dictionary.csv` | Field definitions, printed units, evidence classes and direct NBS table URLs | Provenance/data dictionary |
| `nbs_2024_national_benchmarks.csv` | Printed national totals used to reconcile the 31 province rows | Official public benchmark transcription |
| `source_catalog.csv` | URLs, access status, licensing/terms notes and repository mapping | Provenance catalog |
| `public_data_catalog.xlsx` | Review-friendly workbook containing every CSV table, a data dictionary and quality-control checks | Derived packaging only |

Refresh the online snapshots with:

```powershell
python -m fishery_repro public-data
```

The World Bank/FAO and Ministry series use different statistical definitions and
must not be merged without checking scope. The former province-level NBS `A0407`
endpoint returned HTTP 403 during automated retrieval. The repository therefore
uses the official yearbook tables instead; Table 12-15 supplies all 31
province-level aquatic-product rows directly. No values were guessed or copied
from paywalled aggregators.

For the detailed files, `reported_value` and `reported_unit` preserve the official
page presentation. `normalization_multiplier`, `value`, and `unit` show the exact
machine-readable conversion (for example, 万吨 × 10,000 = tonnes). `source_sha256`
identifies the downloaded HTML used by the parser. The public-data tests reconcile
headline totals and components while allowing only the small rounding differences
explicitly noted in the Ministry communique.
