# Algorithm implementation details

## Decision representation

`FisheryPPMSProblem.decode` reshapes each normalized vector into
`X[candidate, region, sector, mode]` with dimensions `31 × 4 × 2 = 248`.
Multiplication by `ub_amount` converts every normalized entry to tonnes.

## Objectives

The public surrogate returns three maximization scores in `[0, 1]`, while `pymoo`
receives their negatives because it minimizes:

- social reliability: income-weighted allocated volume divided by regional workforce;
- economic efficiency: digitally moderated value minus cost;
- ecological security: ecological sector weights plus a national capture-pressure term.

All intermediate arrays are returned by `evaluate_components`, allowing an
independent recalculation from saved decision vectors.

## Constraints

Each residual is feasible when `g <= 0`:

1. national capture divided by TAC minus one;
2. capture share minus 0.28;
3. processed volume divided by national processing capacity minus one;
4. total supply divided by its upper limit minus one;
5. maximum regional processing/cold-capacity excess;
6. minimum required supply divided by actual supply minus one;
7. fleet-power demand divided by its limit minus one.

## IA-NSGA-III additions

`ChaoticSampling` generates the initial population with
`z(t+1) = μ z(t) [1-z(t)]`, where `μ=4.0`.

`FisheryPPMSProblem.repair` performs three deterministic feedback passes. Each pass
scales capture variables toward TAC feasibility, scales regional processed output to
cold-storage capacity, and raises aquaculture allocations when total supply is below
its minimum. Constraints not eliminated by repair remain explicit selection pressure.

`GenerationAuditCallback` relocates reference directions every configured `ω`
generations. Feasible objective vectors are min-max normalized and projected to the
unit simplex. Each direction moves by `γ` toward its nearest objective ray and is then
renormalized. Every relocation magnitude is saved.

The bundled `pymoo` MOEA/D implementation accepts only unconstrained problems.
`ConstraintPenaltyProblem` therefore exposes the documented penalty
`F_penalized = -F + 100 * sum(max(g,0))` to MOEA/D. Logging and final exports always
re-evaluate the original seven residuals through `FisheryPPMSProblem`, so the penalty
view cannot conceal infeasible solutions.

## Source map

- Model and repair: `src/fishery_repro/model.py`
- Operators and algorithm construction: `src/fishery_repro/benchmark.py`
- Repeats, logging and metrics: `src/fishery_repro/experiment.py`
- Per-figure schema and transformations: `src/fishery_repro/result_pipeline.py`
