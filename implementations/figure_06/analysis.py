"""Self-contained audit entry for article Figure 6.

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
FIGURE_NUMBER = 6
TITLE = 'Parameter sensitivity'
DATA_STATUS = "经过处理的数据 / processed data; not author-run logs"
INPUT_FILE = 'input_data.csv'
EXPECTED_COLUMNS = {'parameter': {'kind': 'string', 'nullable': False, 'minimum': None, 'maximum': None, 'allowed': ('adaptive_factor', 'relocation_frequency')}, 'setting': {'kind': 'number', 'nullable': False, 'minimum': 0, 'maximum': None, 'allowed': None}, 'hv': {'kind': 'number', 'nullable': False, 'minimum': 0, 'maximum': 1, 'allowed': None}, 'sd': {'kind': 'number', 'nullable': False, 'minimum': 0, 'maximum': 1, 'allowed': None}}
UNIQUE_KEY = ('parameter', 'setting')
TRANSFORMATIONS = ('Compute lower and upper one-SD bands.', 'Rank settings by HV within each parameter and identify the optimum.')


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
