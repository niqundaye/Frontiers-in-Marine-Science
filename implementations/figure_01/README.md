# 图 1：PPMS-MOO and IA-NSGA-III architecture

数据性质：**经过处理的数据 / processed data**。这里的结构化 CSV 与派生结果不是作者原始运行日志。

## 文件与审计链

- `analysis.py`：本图的独立代码入口，显式列出字段模式、唯一键和变换步骤；
- 本图为结构图，不使用数值输入；组件清单写入 `derived_data.csv`。
- `derived_data.csv`：由输入计算的统计量、排名、斜率或非支配标记；
- `validation_report.json`：输入 SHA-256、行列数、模式和语义校验；
- `Figure_01_PPMS_MOO_architecture.png`：从用户提供的 316Manuscript.DOCX 提取并组合的论文结果图；
- `generated_from_processed_data/`：代码根据经过处理的数据生成的 PNG/SVG 对照图；
- 共享的完整校验/统计实现：`../../src/fishery_repro/result_pipeline.py`；
- 共享绘图实现：`../../src/fishery_repro/figures.py`。

## 本图的数据处理

1. Declare the 31 x 4 x 2 decision tensor.
2. Map three objectives and seven inequality constraints.
3. Connect chaotic sampling, constraint repair and adaptive reference relocation.

## 独立运行

```powershell
.venv\Scripts\python implementations/figure_01/analysis.py
```
