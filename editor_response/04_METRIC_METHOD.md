# HV and IGD calculation record

## Newly executed surrogate runs

The new verification experiment uses four algorithms and 30 independent seeds
per algorithm. It uses a reduced executable budget of 48 individuals and 30
generations; it is therefore a technical audit run, not a rerun of the article's
reported 200-individual, 1,000-generation experiment.

For every final population:

1. the maximisation objectives are `social_reliability`,
   `economic_efficiency`, and `ecological_security`;
2. feasible solutions are used when present; otherwise all final solutions are
   used and this fallback is recorded in `metric_population`;
3. objective scores are converted to minimisation costs by `cost = 1 - score`;
4. HV is evaluated against the fixed minimisation reference point
   `(1.05, 1.05, 1.05)`;
5. IGD is evaluated against the pooled non-dominated cost front formed from all
   final-population solutions in this new experiment;
6. `pooled_reference_front.csv` stores that front, and
   `metric_recomputation_check.csv` independently recalculates every run's HV
   and IGD and compares them with `run_summary.csv`.

Because the article did not publish its objective normalisation constants, HV
reference point, or IGD reference set, the new-run metrics cannot be interpreted
as the original reported HV/IGD values.

## Article Figure 3 calibrated values

`runs/article_figure3_calibrated/figure_03_calibrated_30run_metrics.csv` contains
30 HV and 30 IGD values per algorithm. They were generated deterministically
from the manuscript-reported means/dispersion anchors using seed 1809036. They
are supplied only to make the plotted distribution reproducible. They are not
measurements recovered from the historical optimisation runs.
