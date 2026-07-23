from pathlib import Path
import sys

import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fishery_repro.figures import _style, figure_03

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    _style()
    paths = figure_03(pd.read_csv(HERE / 'input_data.csv'), HERE, ("png", "svg"), 220)
    for path in paths:
        print(path.resolve())
