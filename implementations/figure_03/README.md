# 图 3：Thirty-run statistical comparison

数据性质：**经过处理的数据 / processed data**。这里的结构化 CSV 与派生结果不是作者原始运行日志。

## 文件与审计链

- `analysis.py`：本图的独立代码入口，显式列出字段模式、唯一键和变换步骤；
- `input_data.csv`：绘图与分析入口，明确标识为“经过处理的数据”；
- `derived_data.csv`：由输入计算的统计量、排名、斜率或非支配标记；
- `validation_report.json`：输入 SHA-256、行列数、模式和语义校验；
- `Figure_03_statistical_comparison.png`：从用户提供的 316Manuscript.DOCX 提取并组合的论文结果图；
- `generated_from_processed_data/`：代码根据经过处理的数据生成的 PNG/SVG 对照图；
- 共享的完整校验/统计实现：`../../src/fishery_repro/result_pipeline.py`；
- 共享绘图实现：`../../src/fishery_repro/figures.py`。

## 本图的数据处理

1. Verify exactly 30 independent run identifiers per algorithm-metric cell.
2. Compute mean, sample SD, median, quartiles, minimum and maximum.

## 独立运行

```powershell
.venv\Scripts\python implementations/figure_03/analysis.py
```
