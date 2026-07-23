"""Self-contained audit entry for article Figure 2.

The validation and transformations are implemented in
``fishery_repro.result_pipeline`` and unit tested at repository level.  This
file declares the exact contract for this individual result.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fishery_repro.result_pipeline import run_figure_pipeline

HERE = Path(__file__).resolve().parent
FIGURE_NUMBER = 2
TITLE = 'Convergence comparison'
DATA_STATUS = "经过处理的数据 / processed data; not author-run logs"
INPUT_FILE = 'input_data.csv'
EXPECTED_COLUMNS = {'generation': {'kind': 'number', 'nullable': False, 'minimum': 0, 'maximum': 1000, 'allowed': None}, 'algorithm': {'kind': 'string', 'nullable': False, 'minimum': None, 'maximum': None, 'allowed': ('IA-NSGA-III', 'NSGA-III', 'MOEA/D', 'NSGA-II')}, 'value': {'kind': 'number', 'nullable': False, 'minimum': 0, 'maximum': 1, 'allowed': None}, 'metric': {'kind': 'string', 'nullable': False, 'minimum': None, 'maximum': None, 'allowed': ('HV', 'IGD')}}
UNIQUE_KEY = ('generation', 'algorithm', 'metric')
TRANSFORMATIONS = ('Sort each algorithm-metric trajectory by generation.', 'Integrate each curve by the trapezoidal rule.', 'Report initial, terminal and absolute change values.')


def main() -> None:
    """Validate input, write derived data/audit JSON, and render PNG plus SVG."""
    print(json.dumps({
        "figure": FIGURE_NUMBER,
        "title": TITLE,
        "data_status": DATA_STATUS,
        "input_file": INPUT_FILE,
        "expected_columns": EXPECTED_COLUMNS,
        "unique_key": UNIQUE_KEY,
        "transformations": TRANSFORMATIONS,
    }, ensure_ascii=False, indent=2))
    outputs = run_figure_pipeline(FIGURE_NUMBER, HERE, formats=("png", "svg"), dpi=220)
    print(outputs["derived_data"].resolve())
    print(outputs["validation_report"].resolve())
    for plot in outputs["plots"]:
        print(plot.resolve())


if __name__ == "__main__":
    main()
