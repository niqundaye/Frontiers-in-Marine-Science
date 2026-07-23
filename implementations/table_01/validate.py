from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent / "data.csv"

if __name__ == "__main__":
    frame = pd.read_csv(DATA)
    assert len(frame) == 3, f"expected 3 rows, got {len(frame)}"
    assert not frame.empty
    print(frame.to_string(index=False))
    print(f"validated rows={len(frame)}, columns={len(frame.columns)}")
