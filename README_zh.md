# 中国渔业 IA-NSGA-III 论文复现包

本仓库复现论文：

> Liu, N., Mao, N., & Huang, J. (2026). *Optimizing sustainable fishery resource allocation in China: an improved adaptive NSGA-III approach under multi-dimensional rigid constraints*. Frontiers in Marine Science, 13, 1809036. https://doi.org/10.3389/fmars.2026.1809036

已完成的内容包括：

- 从 `316Manuscript.DOCX` 提取并组合论文图 1-10，作为主要实验结果图；
- 使用结构化 CSV 生成的 PNG/SVG 代码对照图；
- 论文 4 个表的结构化 CSV；
- 图 2-10 的全部绘图数据 CSV；
- 世界银行/FAO 2014-2023 捕捞、养殖和渔业总产量开放数据；
- 可访问农业农村部年度公报的机器可读提取及来源清单；
- 每张图、每个表均有代码、输入数据和输出结果同目录的独立实现包；
- 248 维生产—加工—营销（PPMS）约束优化模型；
- Logistic 混沌初始化、约束违反反馈修复、自适应参考点迁移；
- NSGA-III、NSGA-II 的可运行烟雾测试；
- 自动测试、GitHub Actions 和 SHA-256 结果清单。

## 重要边界

这不是“作者原始运行日志的严格数值复刻”。截至 2026-07-23，期刊页面没有提供可下载的补充数据或源码；论文也没有公开 31 省的完整输入矩阵、区域 TAC、数字化指数底层指标、收入/成本系数和 30 次独立运行日志。

因此，本仓库统一使用“经过处理的数据”标识，并按来源保留说明：

- **精确转录**：正文表 1-4 和明确披露的数值；
- **经过处理的数据（公开来源）**：世界银行/FAO 数据和农业农村部公报中的全国数据；
- **经过处理的数据（论文原图）**：从 `316Manuscript.DOCX` 直接提取的 20 张原始子图，并仅进行多子图排版；
- **经过处理的数据（代码重绘）**：图 2-10 中未公开的逐点值依据论文曲线与数值锚点整理，用于可运行代码对照；
- **公开代理模型**：保留 248 维结构和约束逻辑，但未披露的省级系数采用可替换代理值。

不要把 `results/data/` 中经过处理的数据称为作者原始 30 次运行日志。

## 一键运行

```powershell
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m fishery_repro all
.venv\Scripts\python -m fishery_repro public-data
.venv\Scripts\python -m pytest
```

如需从同一版本的 Word 稿重新导入论文原图：

```powershell
.venv\Scripts\python scripts\import_manuscript_figures.py "路径\316Manuscript.DOCX"
```

主要 DOCX 原图结果位于 `results/figures/`，代码对照图位于 `results/processed_data_replots/`，逐项实现包位于 `implementations/`，经过处理的数据位于 `data/processed/` 和 `data/public/`。若后续获得作者原始省级数据，只需替换 `FisheryPPMSProblem` 中的代理系数来源，即可把当前“结构复现”升级为“严格数值复现”。
