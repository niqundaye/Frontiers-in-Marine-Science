# Reproducibility report

## Result map

| Article item | Repository source | Evidence level |
|---|---|---|
| Figure 1, PPMS-MOO architecture | `figures.figure_01` | Conceptual recreation |
| Figure 2, HV/IGD convergence | `results/data/figure_02_convergence.csv` | Calibrated reconstruction |
| Figure 3, 30-run boxplots | `results/data/figure_03_boxplots.csv` | Reported-anchor reconstruction |
| Figure 4, KPI radar | `results/data/figure_04_kpis.csv` | Reported-trend reconstruction |
| Figure 5, 3D Pareto sets | `results/data/figure_05_pareto.csv` | Calibrated reconstruction |
| Figure 6, parameter sensitivity | `results/data/figure_06_parameter_sensitivity.csv` | Digitized-anchor reconstruction |
| Figure 7, digitalization sensitivity | `results/data/figure_07_digitalization_sensitivity.csv` | Reported-trend reconstruction |
| Figure 8, TAC sensitivity | `results/data/figure_08_tac_sensitivity.csv` | Reported-anchor reconstruction |
| Figure 9, algorithm ablation | `results/data/figure_09_algorithm_ablation.csv` | Reported-trend reconstruction |
| Figure 10, module ablation | `results/data/figure_10_module_ablation.csv` | Printed-value reconstruction |
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

