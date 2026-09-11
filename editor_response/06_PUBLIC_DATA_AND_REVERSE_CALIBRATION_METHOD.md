# 31-province public-data panel and reverse-calibration method

## Evidentiary status

This method supplies a reproducible replacement for inputs that are absent from
the retained historical archive. It does **not** recover the authors' original
31-province workbook. The package deliberately keeps three evidence layers
separate:

1. **Official public observations** — values transcribed from six National
   Bureau of Statistics (NBS) tables for all 31 mainland province-level regions.
2. **Processed/calibrated inputs** — deterministic transformations that connect
   the 2024 public observations to the paper's disclosed 2023 national anchors
   and 31 x 4 x 2 decision structure.
3. **New optimisation outputs** — runs executed with the disclosed replacement
   inputs and retained configuration; these are not the missing historical logs.

The first layer is labeled `official public data; ... not historical author
input`. The second layer is labeled `calibrated reconstruction; not historical
author input`. A value from either layer must not be described as a recovered
original.

## Official 31-province observations

All observations refer to 2024 and were accessed on 11 September 2026 through
the official *China Statistical Yearbook 2025* navigation page:
<https://www.stats.gov.cn/sj/ndsj/2025/left_.htm>.

| Model domain | NBS table and direct URL | Retained fields | Use in reconstruction |
|---|---|---|---|
| Production | [12-15 Output of Aquatic Products](https://www.stats.gov.cn/sj/ndsj/2025/html/E12-15.jpg) | total, marine/freshwater, capture/aquaculture | Direct regional-sector backbone |
| Social | [2-5 Population at Year-end by Region](https://www.stats.gov.cn/sj/ndsj/2025/html/E02-05.jpg) | year-end population | Workforce-allocation proxy |
| Economic | [6-18 Per Capita Disposable Income](https://www.stats.gov.cn/sj/ndsj/2025/html/E06-18.jpg) | disposable income per person | Economic and social-need multipliers |
| Ecological | [8-10 Main Pollutants in Wastewater](https://www.stats.gov.cn/sj/ndsj/2025/html/E08-10.jpg) | COD and total phosphorus | External pressure proxy |
| Processing/marketing logistics | [16-13 Freight Traffic](https://www.stats.gov.cn/sj/ndsj/2025/html/E16-13.jpg) | total freight | Logistics and cold-capacity proxy |
| Digital marketing | [16-39 Informatization and E-Commerce](https://www.stats.gov.cn/sj/ndsj/2025/html/E16-39.jpg) | enterprise counts, e-commerce enterprise counts and sales | External digitalisation proxy |

The complete transcription is
`data/source/nbs_2024_31_province_public_panel.csv`; its field-level definitions
and URLs are in the adjacent dictionary file. The `Public Data QC` worksheet
reconciles province sums to each printed national total. It preserves documented
scope differences: the population national total includes military personnel,
and national freight includes 97,072 (10,000 tonnes) not classified by region.
Aquatic-product component differences of up to 0.3 (10,000 tonnes) are consistent
with the one-decimal precision printed by NBS.

## Reverse-calibration equations

Let \(y_{rs}^{2024}\) be the official 2024 output in tonnes for province \(r\)
and sector \(s\), where the four sectors are marine capture, freshwater capture,
marine aquaculture and freshwater aquaculture. Let the paper's 2023 national
production anchor be \(Y^{paper}=71{,}161{,}716\) tonnes.

The national scaling factor and calibrated province-sector baseline are

\[
k=\frac{Y^{paper}}{\sum_r\sum_s y_{rs}^{2024}},\qquad
\tilde y_{rs}=k y_{rs}^{2024}.
\]

This preserves the observed 2024 spatial-sector composition while matching the
paper's 2023 national total. It is a transparent temporal-proxy assumption, not
an assertion that the 2024 observations were used by the authors.

The paper requires two utilisation modes but does not disclose their provincial
values. The following sector-specific fresh-sales/deep-processing shares are
declared assumptions:

| Sector | Fresh sales | Deep processing |
|---|---:|---:|
| Marine capture | 0.62 | 0.38 |
| Freshwater capture | 0.67 | 0.33 |
| Marine aquaculture | 0.74 | 0.26 |
| Freshwater aquaculture | 0.78 | 0.22 |

For mode \(m\), the processed baseline and decision upper bound are

\[
b_{rsm}=\tilde y_{rs}q_{sm},\qquad u_{rsm}=1.20b_{rsm}.
\]

The 20% headroom is a declared surrogate-model rule. Every one of the 248 rows
in `coefficient_matrix_248_rows.csv` contains the official sector observation,
calibrated sector value, assumed mode share, processed baseline and final upper
bound, allowing the chain to be recomputed without hidden steps.

## Public-proxy construction

The remaining unreleased province coefficients are generated deterministically:

- **Digital index:** 0.25 plus 0.70 times a composite of 60% min-max normalised
  e-commerce adoption and 40% min-max normalised log e-commerce sales per
  enterprise.
- **Economic multiplier:** provincial disposable income divided by the 2024
  national average, clipped to [0.65, 1.45].
- **Social-need multiplier:** the inverse income ratio, clipped to the same
  interval.
- **Ecological-pressure index:** min-max normalised log of
  `(COD + 20 x total phosphorus) / population`. This is a general wastewater
  proxy and must not be called a fishery habitat or water-quality observation.
- **Freight index:** min-max normalised log regional freight traffic.
- **Workforce:** the disclosed 11,762,300 national anchor distributed by a
  normalised weight of 75% production share and 25% population share.
- **Cold capacity:** calibrated province production multiplied by
  `0.18 + 0.22 x freight_index`.
- **Fleet power:** the disclosed 18,940,154 kW national anchor distributed by
  calibrated capture output plus 5% of calibrated total output.

The executable implementation is in `code/model.py`; the exact table builder is
`code/build_editor_response_data.py`. The workbook `Derivation Rules` and
`Variable Dictionary` sheets repeat these formulas beside the values.

## Mapping to the editor's four requests

1. **31-province coefficient/input matrix:** the public observation sheet and
   248-row processed matrix provide a complete, inspectable replacement; the
   historical original remains unavailable.
2. **Underlying source files:** the package supplies the six-table transcription,
   national benchmarks, field dictionary, source catalogue and direct official
   URLs. They are replacement public sources, not the absent contemporaneous
   workbooks.
3. **30-run outputs:** `runs/new_30run_surrogate/` contains newly executed logs
   and independently recomputed HV/IGD values using the replacement model.
4. **Exact unavailable scope and reason:** `02_Material_Availability.csv` states
   each absent file/variable and the evidence-based reason. The available record
   does not establish whether the originals are stored elsewhere, were deleted,
   or were never exported.

## Appropriate claim

The strongest supportable statement is: “A 31-province official-public-data
panel and a fully documented processed/calibrated input matrix are supplied for
independent verification and rerunning.” It is not supportable to state that the
matrix or the new optimisation logs are the materials originally used to produce
the published numerical results.
