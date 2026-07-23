# Public online data

This directory contains openly retrievable data added after the article reconstruction.

| File | Contents | Evidence level |
|---|---|---|
| `world_bank_fao_china_fisheries_2014_2023.csv` | China total, aquaculture and capture production from FAO via the World Bank API | 经过处理的数据（公开来源），CC BY 4.0 |
| `moa_national_fishery_statistics.csv` | Key values parsed from accessible Ministry annual communiqués | 经过处理的数据（官方公报） |
| `source_catalog.csv` | URLs, access status, licensing/terms notes and repository mapping | Provenance catalog |
| `public_data_catalog.xlsx` | Review-friendly workbook containing all three CSV tables and notes | Derived packaging only |

Refresh the online snapshots with:

```powershell
python -m fishery_repro public-data
```

The World Bank/FAO and Ministry series use different statistical definitions and must not be merged without checking scope. Province-level NBS indicator `A0407` is documented in the source catalog, but its automated endpoint returned HTTP 403 during retrieval, so no values were guessed or copied from paywalled aggregators.
