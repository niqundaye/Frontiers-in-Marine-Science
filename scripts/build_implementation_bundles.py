from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATIONS = ROOT / "implementations"

FIGURES = {
    1: ("Figure_01_PPMS_MOO_architecture", None, "PPMS-MOO 架构图"),
    2: ("Figure_02_convergence", "figure_02_convergence.csv", "HV/IGD 收敛曲线"),
    3: ("Figure_03_statistical_comparison", "figure_03_boxplots.csv", "30 次运行箱线图"),
    4: ("Figure_04_kpi_radar", "figure_04_kpis.csv", "三目标 KPI 雷达图"),
    5: ("Figure_05_pareto_sets", "figure_05_pareto.csv", "三维 Pareto 集"),
    6: ("Figure_06_parameter_sensitivity", "figure_06_parameter_sensitivity.csv", "参数敏感性"),
    7: ("Figure_07_digitalization_sensitivity", "figure_07_digitalization_sensitivity.csv", "数字化系数敏感性"),
    8: ("Figure_08_tac_sensitivity", "figure_08_tac_sensitivity.csv", "TAC 政策敏感性"),
    9: ("Figure_09_algorithm_ablation", "figure_09_algorithm_ablation.csv", "算法组件消融"),
    10: ("Figure_10_module_ablation", "figure_10_module_ablation.csv", "PPM 模块消融"),
}

TABLES = {
    1: ("table_1_decision_indices.csv", 3),
    2: ("table_2_economic_welfare.csv", 10),
    3: ("table_3_capacity_constraints.csv", 10),
    4: ("table_4_algorithm_parameters.csv", 14),
}


def _figure_runner(number: int, input_name: str | None) -> str:
    function = f"figure_{number:02d}"
    data_import = "import pandas as pd\n" if input_name else ""
    call_arg = "pd.read_csv(HERE / 'input_data.csv'), " if input_name else ""
    return f'''from pathlib import Path
import sys

{data_import}ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fishery_repro.figures import _style, {function}

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    _style()
    output = HERE / "generated_from_processed_data"
    output.mkdir(parents=True, exist_ok=True)
    paths = {function}({call_arg}output, ("png", "svg"), 220)
    for path in paths:
        print(path.resolve())
'''


def build_figures() -> None:
    for number, (stem, input_name, evidence) in FIGURES.items():
        bundle = IMPLEMENTATIONS / f"figure_{number:02d}"
        bundle.mkdir(parents=True, exist_ok=True)
        (bundle / "run.py").write_text(_figure_runner(number, input_name), encoding="utf-8")
        for stale_svg in bundle.glob("Figure_*.svg"):
            stale_svg.unlink()
        if input_name:
            shutil.copy2(ROOT / "results" / "data" / input_name, bundle / "input_data.csv")
        shutil.copy2(ROOT / "results" / "figures" / f"{stem}.png", bundle / f"{stem}.png")
        generated = bundle / "generated_from_processed_data"
        generated.mkdir(parents=True, exist_ok=True)
        for extension in ("png", "svg"):
            shutil.copy2(
                ROOT / "results" / "processed_data_replots" / f"{stem}.{extension}",
                generated / f"{stem}.{extension}",
            )
        input_line = "- `input_data.csv`：代码重绘使用的经过处理的数据。\n" if input_name else "- 本图不需要数值输入表。\n"
        readme = f"""# 图 {number} 独立实现包

数据标识：**经过处理的数据**。内容：{evidence}。

## 文件

- `run.py`：本图独立运行入口；
{input_line}- `{stem}.png`：从用户提供的 `316Manuscript.DOCX` 提取并按子图编号排版的主要结果；
- `generated_from_processed_data/`：运行代码后根据结构化数据生成的 PNG/SVG 对照图；
- 共享核心实现：[`src/fishery_repro/figures.py`](../../src/fishery_repro/figures.py)。

## 运行

在仓库根目录完成 `pip install -e .` 后：

```powershell
python implementations/figure_{number:02d}/run.py
```

图 2-10 的 CSV 统一标识为“经过处理的数据”：它们依据论文披露的曲线和数值锚点整理，不是作者原始 30 次运行日志。
"""
        (bundle / "README.md").write_text(readme, encoding="utf-8")


def build_tables() -> None:
    for number, (filename, expected_rows) in TABLES.items():
        bundle = IMPLEMENTATIONS / f"table_{number:02d}"
        bundle.mkdir(parents=True, exist_ok=True)
        source_text = (ROOT / "data" / "paper" / filename).read_text(encoding="utf-8")
        (bundle / "data.csv").write_text(source_text.rstrip("\r\n") + "\n", encoding="utf-8")
        validator = f'''from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent / "data.csv"

if __name__ == "__main__":
    frame = pd.read_csv(DATA)
    assert len(frame) == {expected_rows}, f"expected {expected_rows} rows, got {{len(frame)}}"
    assert not frame.empty
    print(frame.to_string(index=False))
    print(f"validated rows={{len(frame)}}, columns={{len(frame.columns)}}")
'''
        (bundle / "validate.py").write_text(validator, encoding="utf-8")
        (bundle / "README.md").write_text(
            f"""# 表 {number} 独立实现包

- `data.csv`：论文表 {number} 的精确结构化转录；
- `validate.py`：行数、可读性和基本完整性检查；
- 原始集中版本：[`data/paper/{filename}`](../../data/paper/{filename})。

```powershell
python implementations/table_{number:02d}/validate.py
```
""",
            encoding="utf-8",
        )


def build_model_bundle() -> None:
    bundle = IMPLEMENTATIONS / "model_248d"
    bundle.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "results" / "benchmark" / "smoke_summary.csv", bundle / "smoke_summary.csv")
    (bundle / "run.py").write_text(
        '''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fishery_repro.benchmark import run_smoke_benchmark

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    print(run_smoke_benchmark(HERE / "smoke_summary.csv", population=48, generations=20, seed=1809036))
''',
        encoding="utf-8",
    )
    (bundle / "README.md").write_text(
        """# 248 维 PPMS 模型实现包

- `run.py`：IA-NSGA-III 代理实现与 NSGA 基线的烟雾基准入口；
- `smoke_summary.csv`：当前结果；
- [`src/fishery_repro/model.py`](../../src/fishery_repro/model.py)：31×4×2 决策变量、三目标和七类约束；
- [`src/fishery_repro/benchmark.py`](../../src/fishery_repro/benchmark.py)：算法和评价指标实现。

```powershell
python implementations/model_248d/run.py
```

这是可公开运行的结构代理模型；未公开省级系数没有被伪装成作者数据。
""",
        encoding="utf-8",
    )


def build_index() -> None:
    links = [f"- [图 {i:02d}](figure_{i:02d}/README.md)" for i in FIGURES]
    links += [f"- [表 {i:02d}](table_{i:02d}/README.md)" for i in TABLES]
    links += ["- [248 维模型与算法基准](model_248d/README.md)"]
    text = """# 分结果自包含实现包

本目录把每个论文结果所需的**代码、经过处理的数据、DOCX 原图结果、代码重绘结果和说明**放在同一目录中，便于逐项查看和运行。共享数学实现仍保留在 `src/fishery_repro/`，各目录的 `run.py` 或 `validate.py` 是明确的独立入口。

""" + "\n".join(links) + "\n"
    (IMPLEMENTATIONS / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    IMPLEMENTATIONS.mkdir(parents=True, exist_ok=True)
    build_figures()
    build_tables()
    build_model_bundle()
    build_index()
    print(f"Implementation bundles written to {IMPLEMENTATIONS.resolve()}")


if __name__ == "__main__":
    main()
