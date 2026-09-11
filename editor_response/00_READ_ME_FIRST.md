# Response package: original inputs and 30-run logs

Prepared on **2026-09-11** in response to the request for the original
31-province input/coefficient matrix, its source workbooks, and the original
30-run optimisation logs.

## Essential disclosure

The historical files requested by the editor are **not present in the retained
materials available for this response**. The retained materials contain the
manuscript and aggregate tables/figures, but no contemporaneous province input
workbook, preprocessing workbook, or original optimiser output directory. The
available evidence does not establish whether those files are stored elsewhere,
were deleted, or were never exported as standalone files.

Nothing in this package is represented as a recovered historical original.

## What this package provides

1. `01_Response_to_Editor_DRAFT.docx` and PDF: a point-by-point response.
2. `02_Material_Availability.csv`: exact inventory of unavailable materials.
3. `03_Reconstructed_31_Province_Inputs.xlsx`: an auditable workbook containing
   the 31-region proxy inputs, the complete 248-row coefficient matrix, model
   constants, source mapping, and QC checks.
4. `data/reconstructed/`: machine-readable CSV exports of the workbook tables.
5. `data/source/`: article-table transcriptions and public-source extracts used
   for later verification/reconstruction. These are not the historical raw
   spreadsheets used in the reported experiment.
6. `runs/article_figure3_calibrated/`: 30-value-per-algorithm HV/IGD series
   generated from manuscript-reported distribution anchors. These values are
   processed reconstruction, not recovered run logs.
7. `runs/new_30run_surrogate/`: newly executed 30 independent runs per algorithm,
   with generation logs, final solutions, 248-dimensional decision vectors,
   pooled reference front, and independently recomputed HV/IGD checks.
8. `code/`: the exact scripts/configuration used to create the replacement
   materials.
9. `SHA256SUMS.csv`: byte-level inventory of every packaged file.

## Rebuild commands

From the repository root, after installing the pinned environment:

```powershell
.venv\Scripts\python scripts\build_editor_response_data.py
node scripts\build_editor_response_workbook.mjs
.venv\Scripts\python scripts\build_editor_response_letter.py
.venv\Scripts\python scripts\package_editor_response.py
```

The committed run directory is sufficient for offline audit. Re-running the
first command intentionally creates a new replacement experiment under the
declared seed/configuration protocol; it does not recover the historical runs.
Use `node scripts\build_editor_response_workbook.mjs --render-qa` when PNG
previews of every workbook sheet are also required for visual quality review.

## Interpretation rule

The labels `historical original`, `article transcription`, `public source`,
`calibrated reconstruction`, and `new surrogate run` are not interchangeable.
Only a contemporaneous file demonstrably used for the published results may be
called an original. The replacement materials allow technical inspection, but
do not cure the absence of the historical originals.
