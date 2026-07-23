# Data inventory

| Path | Description | Provenance class |
|---|---|---|
| `paper/table_1_decision_indices.csv` | Decision-index definition | Exact article transcription |
| `paper/table_2_economic_welfare.csv` | 2014-2023 economic/welfare table | Exact article transcription |
| `paper/table_3_capacity_constraints.csv` | 2014-2023 production/capacity table | Exact article transcription |
| `paper/table_4_algorithm_parameters.csv` | Algorithm parameter table | Exact article transcription |
| `verified/official_2023_summary.csv` | Independent official checks | Ministry of Agriculture and Rural Affairs communiqué |
| `public/world_bank_fao_china_fisheries_2014_2023.csv` | Open 2014-2023 fisheries, aquaculture and capture series | FAO via World Bank API, CC BY 4.0 |
| `public/moa_national_fishery_statistics.csv` | Machine-readable statistics from accessible official annual communiqués | Ministry of Agriculture and Rural Affairs |
| `public/source_catalog.csv` | URLs, access/licensing notes, and unavailable-source disclosures | Provenance catalog |
| `../results/data/*.csv` | Complete points used to draw Figures 2-10 | Calibrated reconstruction |

The yearbook volumes themselves are not included because their redistribution terms were not established. Run `python -m fishery_repro public-data` to refresh the openly accessible World Bank/FAO and official-communiqué snapshots.
