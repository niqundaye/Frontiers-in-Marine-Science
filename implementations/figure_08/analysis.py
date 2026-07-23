"""Self-contained audit entry for article Figure 8.

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
FIGURE_NUMBER = 8
TITLE = 'TAC policy sensitivity'
DATA_STATUS = "经过处理的数据 / processed data; not author-run logs"
INPUT_FILE = 'input_data.csv'
EXPECTED_COLUMNS = {'record_type': {'kind': 'string', 'nullable': False, 'minimum': None, 'maximum': None, 'allowed': ('pareto', 'hv')}, 'tac': {'kind': 'number', 'nullable': False, 'minimum': 0.9, 'maximum': 1.1, 'allowed': None}, 'social': {'kind': 'number', 'nullable': True, 'minimum': 0, 'maximum': 1, 'allowed': None}, 'economic': {'kind': 'number', 'nullable': True, 'minimum': 0, 'maximum': 1, 'allowed': None}, 'ecological': {'kind': 'number', 'nullable': True, 'minimum': 0, 'maximum': 1, 'allowed': None}, 'hv': {'kind': 'number', 'nullable': True, 'minimum': 0, 'maximum': 1, 'allowed': None}, 'sd': {'kind': 'number', 'nullable': True, 'minimum': 0, 'maximum': 1, 'allowed': None}}
UNIQUE_KEY = ()
TRANSFORMATIONS = ('Validate conditional fields for Pareto and HV record types.', 'Summarize objective centroids and HV uncertainty for every TAC scenario.')


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
