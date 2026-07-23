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
- IA-NSGA-III、NSGA-III、NSGA-II 的多随机种子独立实验；
- 逐代可行率、约束违反、HV、非支配解数量和参考方向迁移日志；
- 每个最终解的 248 维决策向量、三个目标、七类约束残差和解码总量；
- 每张图的输入模式、唯一键、派生统计和 SHA-256 校验报告；
- 自动测试、GitHub Actions 和 SHA-256 结果清单。

## 重要边界

这不是“作者原始运行日志的严格数值复刻”。截至 2026-07-23，期刊页面没有提供可下载的补充数据或源码；论文也没有公开 31 省的完整输入矩阵、区域 TAC、数字化指数底层指标、收入/成本系数和 30 次独立运行日志。

因此，本仓库统一使用“经过处理的数据”标识，并按来源保留说明：

- **精确转录**：正文表 1-4 和明确披露的数值；
- **经过处理的数据（公开来源）**：世界银行/FAO 2014-2023 数据、农业农村部 2024 年 99 项详细渔业统计和 12 项生态环境指标，以及国家统计局全国和浙江 2025 年水产品数据；均保留报告值/单位、标准化值、来源网址、检索日期和网页 SHA-256；
- **经过处理的数据（论文原图）**：从 `316Manuscript.DOCX` 直接提取的 20 张原始子图，并仅进行多子图排版；
- **经过处理的数据（代码重绘）**：图 2-10 中未公开的逐点值依据论文曲线与数值锚点整理，用于可运行代码对照；
- **公开代理模型**：保留 248 维结构和约束逻辑，但未披露的省级系数采用可替换代理值。

不要把 `results/data/` 中经过处理的数据称为作者原始 30 次运行日志。

## 一键运行

```powershell
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python scripts\reproduce_research_artifact.py
```

完整研究包命令依次重建数据和图、运行 `5 个种子 × 3 种算法 × 30 代`
公开代理实验、重建每个结果目录、执行 71 项包级审计和全部单元测试。论文披露的
`200 个体 × 1000 代 × 30 次独立运行`协议完整写在
`configs/experiments/paper_protocol.yaml`；该配置只有在补齐作者未公开省级输入后
才能用于严格数值复现。

## 详细实现和输出

- 算法与模型：`src/fishery_repro/model.py`、`benchmark.py`、`experiment.py`；
- 逐代和逐次运行结果：`results/experiments/processed_demo/`；
- 5×3 次运行摘要：`run_summary.csv` 和 `algorithm_summary.csv`；
- 450 行逐代状态：`generation_log.csv`；
- 720 个最终种群解：`final_population_objectives_constraints.csv`；
- 完整 248 维变量：`final_population_decision_vectors.csv`；
- 参考方向更新：`reference_relocation_log.csv`；
- 配置与运行环境：`config_snapshot.yaml` 和 `run_metadata.json`；
- 图 1–10 独立实现：`implementations/figure_01/` 至 `figure_10/`；
- 表 1–4 独立实现：`implementations/table_01/` 至 `table_04/`；
- 数据字典：`data/DATA_DICTIONARY.md`；
- 实验协议与算法公式：`docs/EXPERIMENT_PROTOCOL.md`、`docs/ALGORITHM_IMPLEMENTATION.md`；
- 复现检查清单：`docs/REPRODUCIBILITY_CHECKLIST.md`。

如需从同一版本的 Word 稿重新导入论文原图：

```powershell
.venv\Scripts\python scripts\import_manuscript_figures.py "路径\316Manuscript.DOCX"
```

主要 DOCX 原图结果位于 `results/figures/`，代码对照图位于 `results/processed_data_replots/`，逐项实现包位于 `implementations/`，经过处理的数据位于 `data/processed/` 和 `data/public/`。若后续获得作者原始省级数据，只需替换 `FisheryPPMSProblem` 中的代理系数来源，即可把当前“结构复现”升级为“严格数值复现”。
