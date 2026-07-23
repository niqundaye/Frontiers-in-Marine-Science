from pathlib import Path
import sys

import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fishery_repro.figures import _style, figure_03

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    _style()
    output = HERE / "generated_from_processed_data"
    output.mkdir(parents=True, exist_ok=True)
    paths = figure_03(pd.read_csv(HERE / 'input_data.csv'), output, ("png", "svg"), 220)
    for path in paths:
        print(path.resolve())
