# 图 1 独立实现包

数据标识：**经过处理的数据**。内容：PPMS-MOO 架构图。

## 文件

- `run.py`：本图独立运行入口；
- 本图不需要数值输入表。
- `Figure_01_PPMS_MOO_architecture.png`：从用户提供的 `316Manuscript.DOCX` 提取并按子图编号排版的主要结果；
- `generated_from_processed_data/`：运行代码后根据结构化数据生成的 PNG/SVG 对照图；
- 共享核心实现：[`src/fishery_repro/figures.py`](../../src/fishery_repro/figures.py)。

## 运行

在仓库根目录完成 `pip install -e .` 后：

```powershell
python implementations/figure_01/run.py
```

图 2-10 的 CSV 统一标识为“经过处理的数据”：它们依据论文披露的曲线和数值锚点整理，不是作者原始 30 次运行日志。
