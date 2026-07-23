# Reproducibility report

## Result map

| Article item | Repository source | Evidence level |
|---|---|---|
| Figure 1, PPMS-MOO architecture | `data/processed/manuscript_figures/panels/Figure_01.png` | Processed data: direct DOCX extraction |
| Figure 2, HV/IGD convergence | `data/processed/manuscript_figures/panels/Figure_02*.png`; `results/data/figure_02_convergence.csv` | Processed data: DOCX panels + structured code input |
| Figure 3, 30-run boxplots | `data/processed/manuscript_figures/panels/Figure_03*.png`; `results/data/figure_03_boxplots.csv` | Processed data: DOCX panels + structured code input |
| Figure 4, KPI radar | `data/processed/manuscript_figures/panels/Figure_04.png`; `results/data/figure_04_kpis.csv` | Processed data: DOCX panel + structured code input |
| Figure 5, 3D Pareto sets | `data/processed/manuscript_figures/panels/Figure_05.png`; `results/data/figure_05_pareto.csv` | Processed data: DOCX panel + structured code input |
| Figure 6, parameter sensitivity | `data/processed/manuscript_figures/panels/Figure_06*.png`; `results/data/figure_06_parameter_sensitivity.csv` | Processed data: DOCX panels + structured code input |
| Figure 7, digitalization sensitivity | `data/processed/manuscript_figures/panels/Figure_07*.png`; `results/data/figure_07_digitalization_sensitivity.csv` | Processed data: DOCX panels + structured code input |
| Figure 8, TAC sensitivity | `data/processed/manuscript_figures/panels/Figure_08*.png`; `results/data/figure_08_tac_sensitivity.csv` | Processed data: DOCX panels + structured code input |
| Figure 9, algorithm ablation | `data/processed/manuscript_figures/panels/Figure_09*.png`; `results/data/figure_09_algorithm_ablation.csv` | Processed data: DOCX panels + structured code input |
| Figure 10, module ablation | `data/processed/manuscript_figures/panels/Figure_10*.png`; `results/data/figure_10_module_ablation.csv` | Processed data: DOCX panels + structured code input |
| Tables 1-4 | `data/paper/` | Exact transcription |
| Equations 1-7 / 248-variable structure | `model.FisheryPPMSProblem` | Structural surrogate |

## Findings that prevent strict numerical reproduction

1. The article states that original contributions are in the article/supplementary material, but the published page exposes no supplementary dataset or code archive.
2. The 31-province input matrix and all regional coefficients are absent.
3. The authors' implementation of the “constraint-violation-feedback heuristic operator” is described conceptually but not fully specified.
4. Figure-level run logs and random seeds are absent.
5. IGD is internally inconsistent: the abstract and Section 4.3.2 report `0.012`, while Section 4.3.1 reports a final value of `0.06`.
6. Table 2's displayed monetary unit (`10^4 RMB`) cannot produce the official national total. Interpreting each printed unit as `0.1 × 100 million RMB` makes the 2023 total agree to rounding, but component labels still do not map cleanly to the official communiqué's sector definitions.

## What would upgrade this repository to strict replication

- the province-year harmonized input file;
- regional TAC and fleet-power bounds;
- Entropy Weight Method inputs and weights for the digitalization index;
- sector/mode income, price, cost, ecological-footprint, and processing-conversion coefficients;
- exact crossover/mutation feedback rules and reference relocation association code;
- per-generation objective populations from all 30 runs.
