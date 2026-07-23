from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fishery_repro.benchmark import run_smoke_benchmark

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    print(run_smoke_benchmark(HERE / "smoke_summary.csv", population=24, generations=12, seed=1809036))
