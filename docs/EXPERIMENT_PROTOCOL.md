# Experiment protocol

## Scope and disclosure

The executable experiment is a public-data surrogate of the article's 248-variable
PPMS-MOO problem. It reproduces the disclosed dimensionality, three-objective
structure, seven constraint classes, evolutionary operators, logistic initialization,
constraint-feedback repair and adaptive reference-direction relocation.

It does **not** claim to recover the authors' unpublished 31-province coefficient
matrix or their original 30 independent-run logs. Every generated experimental file
is labelled `经过处理的数据 / public-data surrogate; not author-run logs`.

## Protocols

| YAML | Purpose | Population | Generations | Repeats |
|---|---:|---:|---:|---:|
| `configs/experiments/ci_smoke.yaml` | CI execution-path test | 24 | 8 | 2 per algorithm |
| `configs/experiments/processed_demo.yaml` | Checked-in auditable demonstration | 48 | 30 | 5 per algorithm |
| `configs/experiments/paper_protocol.yaml` | Article-disclosed scale | 200 | 1000 | 30 per algorithm |

The paper-scale file is a protocol declaration, not a claim that its missing private
inputs have been recovered.

## Independent-run procedure

1. Load and validate every YAML field; hidden library defaults are not relied on for
   crossover, mutation, chaotic map or relocation parameters.
2. Initialize the same deterministic surrogate problem for all algorithms.
3. Derive a unique optimizer seed from the declared repeat seed and algorithm index.
4. Execute exactly the declared number of generations without saving opaque Python
   objects.
5. At every generation, record evaluation count, feasible count/fraction, mean and
   maximum total constraint violation, non-dominated count, zero-reference HV and
   maxima for all three objectives.
6. On each declared IA-NSGA-III relocation generation, record the mean reference
   direction shift.
7. Save every final normalized 248-dimensional decision vector and its decoded supply,
   capture, aquaculture, processing, three objectives and seven constraint residuals.
8. Construct a pooled non-dominated reference front from the current experiment only,
   then compute run-level HV and IGD. This IGD is explicitly named
   `igd_to_pooled_reference`; it is not an unreleased author reference set.
9. Save the full configuration snapshot, its SHA-256, timestamps, runtime platform,
   package versions and output row counts in `run_metadata.json`.

## Run

```powershell
.venv\Scripts\python -m fishery_repro experiment `
  --experiment-config configs/experiments/processed_demo.yaml
```

The outputs are written to `results/experiments/processed_demo/`.

