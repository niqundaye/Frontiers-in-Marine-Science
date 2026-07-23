from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fishery_repro.experiment import run_experiment

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    outputs = run_experiment(HERE / "processed_demo.yaml", HERE / "experiment_output")
    for name, path in outputs.items():
        print(f"{name}: {path.resolve()}")
