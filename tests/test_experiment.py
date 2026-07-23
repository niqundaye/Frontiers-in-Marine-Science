import json

import pandas as pd

from fishery_repro.experiment import load_experiment_config, run_experiment
from fishery_repro.model import CONSTRAINT_NAMES, N_VARIABLES


def test_experiment_protocol_and_auditable_outputs(tmp_path):
    config_path = tmp_path / "tiny.yaml"
    config_path.write_text(
        """
name: unit_test
algorithms: [IA-NSGA-III, MOEA/D]
seeds: [1809036]
population: 12
generations: 3
problem_seed: 1809036
save_decision_vectors: true
operator:
  relocation_frequency: 2
  adaptive_factor: 0.1
""".strip(),
        encoding="utf-8",
    )
    config = load_experiment_config(config_path)
    assert config.population == 12
    outputs = run_experiment(config_path, tmp_path / "output")
    generations = pd.read_csv(outputs["generation_log"])
    final = pd.read_csv(outputs["final_solutions"])
    decisions = pd.read_csv(outputs["decision_vectors"])
    metadata = json.loads(outputs["metadata"].read_text(encoding="utf-8"))

    assert generations.groupby("algorithm")["generation"].nunique().eq(3).all()
    assert len([column for column in final if column.startswith("g_")]) == len(CONSTRAINT_NAMES)
    assert len([column for column in decisions if column.startswith("x_r")]) == N_VARIABLES
    assert metadata["model_dimensions"]["decision_variables"] == N_VARIABLES
