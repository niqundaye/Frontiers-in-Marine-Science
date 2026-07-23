from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fishery_repro.result_pipeline import FIGURE_SPECS, run_figure_pipeline


IMPLEMENTATIONS = ROOT / "implementations"
FIGURE_STEMS = {
    1: "Figure_01_PPMS_MOO_architecture",
    2: "Figure_02_convergence",
    3: "Figure_03_statistical_comparison",
    4: "Figure_04_kpi_radar",
    5: "Figure_05_pareto_sets",
    6: "Figure_06_parameter_sensitivity",
    7: "Figure_07_digitalization_sensitivity",
    8: "Figure_08_tac_sensitivity",
    9: "Figure_09_algorithm_ablation",
    10: "Figure_10_module_ablation",
}
RESULT_DATA = {
    2: "figure_02_convergence.csv",
    3: "figure_03_boxplots.csv",
    4: "figure_04_kpis.csv",
    5: "figure_05_pareto.csv",
    6: "figure_06_parameter_sensitivity.csv",
    7: "figure_07_digitalization_sensitivity.csv",
    8: "figure_08_tac_sensitivity.csv",
    9: "figure_09_algorithm_ablation.csv",
    10: "figure_10_module_ablation.csv",
}
TABLES = {
    1: ("table_1_decision_indices.csv", 3),
    2: ("table_2_economic_welfare.csv", 10),
    3: ("table_3_capacity_constraints.csv", 10),
    4: ("table_4_algorithm_parameters.csv", 14),
}


def _analysis_source(number: int) -> str:
    spec = FIGURE_SPECS[number]
    columns = {
        name: {
            "kind": rule.kind,
            "nullable": rule.nullable,
            "minimum": rule.minimum,
            "maximum": rule.maximum,
            "allowed": rule.allowed,
        }
        for name, rule in spec.columns.items()
    }
    return f'''"""Self-contained audit entry for article Figure {number}.

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
FIGURE_NUMBER = {number}
TITLE = {spec.title!r}
DATA_STATUS = "经过处理的数据 / processed data; not author-run logs"
INPUT_FILE = {spec.input_file!r}
EXPECTED_COLUMNS = {columns!r}
UNIQUE_KEY = {spec.unique_key!r}
TRANSFORMATIONS = {spec.transformations!r}


def main() -> None:
    """Validate input, write derived data/audit JSON, and render PNG plus SVG."""
    print(json.dumps({{
        "figure": FIGURE_NUMBER,
        "title": TITLE,
        "data_status": DATA_STATUS,
        "input_file": INPUT_FILE,
        "expected_columns": EXPECTED_COLUMNS,
        "unique_key": UNIQUE_KEY,
        "transformations": TRANSFORMATIONS,
    }}, ensure_ascii=False, indent=2))
    outputs = run_figure_pipeline(FIGURE_NUMBER, HERE, formats=("png", "svg"), dpi=220)
    print(outputs["derived_data"].resolve())
    print(outputs["validation_report"].resolve())
    for plot in outputs["plots"]:
        print(plot.resolve())


if __name__ == "__main__":
    main()
'''


def _figure_readme(number: int) -> str:
    spec = FIGURE_SPECS[number]
    input_line = (
        "- `input_data.csv`：绘图与分析入口，明确标识为“经过处理的数据”；\n"
        if spec.input_file
        else "- 本图为结构图，不使用数值输入；组件清单写入 `derived_data.csv`。\n"
    )
    transformations = "\n".join(
        f"{index}. {step}" for index, step in enumerate(spec.transformations, start=1)
    )
    return f"""# 图 {number}：{spec.title}

数据性质：**经过处理的数据 / processed data**。这里的结构化 CSV 与派生结果不是作者原始运行日志。

## 文件与审计链

- `analysis.py`：本图的独立代码入口，显式列出字段模式、唯一键和变换步骤；
{input_line}- `derived_data.csv`：由输入计算的统计量、排名、斜率或非支配标记；
- `validation_report.json`：输入 SHA-256、行列数、模式和语义校验；
- `{FIGURE_STEMS[number]}.png`：从用户提供的 316Manuscript.DOCX 提取并组合的论文结果图；
- `generated_from_processed_data/`：代码根据经过处理的数据生成的 PNG/SVG 对照图；
- 共享的完整校验/统计实现：`../../src/fishery_repro/result_pipeline.py`；
- 共享绘图实现：`../../src/fishery_repro/figures.py`。

## 本图的数据处理

{transformations}

## 独立运行

```powershell
.venv\\Scripts\\python implementations/figure_{number:02d}/analysis.py
```
"""


def build_figures() -> None:
    for number, stem in FIGURE_STEMS.items():
        bundle = IMPLEMENTATIONS / f"figure_{number:02d}"
        bundle.mkdir(parents=True, exist_ok=True)
        (bundle / "analysis.py").write_text(_analysis_source(number), encoding="utf-8")
        (bundle / "run.py").write_text(
            "from analysis import main\n\nif __name__ == '__main__':\n    main()\n",
            encoding="utf-8",
        )
        (bundle / "README.md").write_text(_figure_readme(number), encoding="utf-8")
        if number in RESULT_DATA:
            shutil.copy2(ROOT / "results" / "data" / RESULT_DATA[number], bundle / "input_data.csv")
        shutil.copy2(ROOT / "results" / "figures" / f"{stem}.png", bundle / f"{stem}.png")
        run_figure_pipeline(number, bundle, formats=("png", "svg"), dpi=220)


def _table_analysis_source(number: int, expected_rows: int, columns: list[str]) -> str:
    return f'''"""Schema, integrity and descriptive audit for article Table {number}."""
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data.csv"
EXPECTED_ROWS = {expected_rows}
EXPECTED_COLUMNS = {columns!r}
DATA_STATUS = "论文表格精确转录 / exact article-table transcription"


def main() -> None:
    raw = DATA.read_bytes()
    frame = pd.read_csv(DATA)
    errors = []
    if len(frame) != EXPECTED_ROWS:
        errors.append(f"expected {{EXPECTED_ROWS}} rows, observed {{len(frame)}}")
    if list(frame.columns) != EXPECTED_COLUMNS:
        errors.append(f"unexpected columns: {{list(frame.columns)}}")
    if frame.empty:
        errors.append("table is empty")
    if frame.isna().all(axis=1).any():
        errors.append("one or more rows are entirely null")
    numeric = frame.select_dtypes(include="number")
    if not numeric.empty and not np.isfinite(numeric.to_numpy(float)).all():
        errors.append("non-finite numeric value")
    report = {{
        "schema_version": "1.0",
        "table": {number},
        "data_status": DATA_STATUS,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(frame),
        "columns": list(frame.columns),
        "numeric_summary": numeric.describe().to_dict(),
        "errors": errors,
        "status": "pass" if not errors else "fail",
    }}
    (HERE / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if errors:
        raise ValueError("; ".join(errors))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''


def build_tables() -> None:
    for number, (filename, expected_rows) in TABLES.items():
        bundle = IMPLEMENTATIONS / f"table_{number:02d}"
        bundle.mkdir(parents=True, exist_ok=True)
        source = ROOT / "data" / "paper" / filename
        normalized_csv = source.read_text(encoding="utf-8").rstrip("\r\n") + "\n"
        (bundle / "data.csv").write_text(normalized_csv, encoding="utf-8")
        columns = list(pd.read_csv(source).columns)
        analysis = _table_analysis_source(number, expected_rows, columns)
        (bundle / "analysis.py").write_text(analysis, encoding="utf-8")
        (bundle / "validate.py").write_text(
            "from analysis import main\n\nif __name__ == '__main__':\n    main()\n",
            encoding="utf-8",
        )
        (bundle / "README.md").write_text(
            f"""# 表 {number} 独立实现包

- `data.csv`：论文表 {number} 的精确结构化转录；
- `analysis.py`：字段顺序、行数、有限数值、摘要统计和 SHA-256 校验；
- `validation_report.json`：机器可读审计结果；
- 原始集中版本：`../../data/paper/{filename}`。

```powershell
.venv\\Scripts\\python implementations/table_{number:02d}/analysis.py
```
""",
            encoding="utf-8",
        )
        frame = pd.read_csv(bundle / "data.csv")
        report = {
            "schema_version": "1.0",
            "table": number,
            "data_status": "论文表格精确转录 / exact article-table transcription",
            "rows": len(frame),
            "columns": list(frame.columns),
            "expected_rows": expected_rows,
            "status": "pass" if len(frame) == expected_rows and list(frame.columns) == columns else "fail",
        }
        (bundle / "validation_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def build_model_bundle() -> None:
    bundle = IMPLEMENTATIONS / "model_248d"
    snapshot = bundle / "source_snapshot"
    snapshot.mkdir(parents=True, exist_ok=True)
    for filename in ("model.py", "benchmark.py", "experiment.py"):
        shutil.copy2(ROOT / "src" / "fishery_repro" / filename, snapshot / filename)
    shutil.copy2(
        ROOT / "configs" / "experiments" / "processed_demo.yaml",
        bundle / "processed_demo.yaml",
    )
    experiment_results = ROOT / "results" / "experiments" / "processed_demo"
    if experiment_results.exists():
        output = bundle / "experiment_output"
        output.mkdir(parents=True, exist_ok=True)
        for path in experiment_results.iterdir():
            if path.is_file():
                shutil.copy2(path, output / path.name)
    (bundle / "run.py").write_text(
        '''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fishery_repro.experiment import run_experiment

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    outputs = run_experiment(HERE / "processed_demo.yaml", HERE / "experiment_output")
    for name, path in outputs.items():
        print(f"{name}: {path.resolve()}")
''',
        encoding="utf-8",
    )
    (bundle / "README.md").write_text(
        """# 248 维 PPMS-MOO 与 IA-NSGA-III 详细实现

此目录不再只是烟雾测试入口：

- `source_snapshot/model.py`：31×4×2 决策张量、三个目标、七个约束与逐步修复；
- `source_snapshot/benchmark.py`：SBX、Polynomial Mutation、参考方向和四类算法构造；
- `source_snapshot/experiment.py`：独立重复、逐代日志、参考方向移动、最终解和运行元数据；
- `processed_demo.yaml`：5 个种子、3 个算法、全部算子参数；
- `experiment_output/`：经过处理的数据，包括逐代日志、最终 248 维决策向量和统计摘要；
- `run.py`：从配置完整重跑上述实验。

这是一套公开代理模型，不是作者未公开的省级输入矩阵或原始 30 次日志。

```powershell
.venv\\Scripts\\python implementations/model_248d/run.py
```
""",
        encoding="utf-8",
    )


def build_index() -> None:
    links = [f"- [图 {number:02d}](figure_{number:02d}/README.md)" for number in FIGURE_STEMS]
    links += [f"- [表 {number:02d}](table_{number:02d}/README.md)" for number in TABLES]
    links += ["- [248 维模型与完整实验](model_248d/README.md)"]
    text = """# 分结果、自包含实现包

每个结果目录同时提供代码、输入数据、派生数据、论文原图、代码重绘图和机器可读校验报告。
共享算法没有隐藏在 notebook 中，而是位于 `src/fishery_repro/` 并由单元测试覆盖；每个目录的
`analysis.py` 显式声明自己的字段模式、唯一键和数据变换。

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
