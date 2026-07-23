# IA-NSGA-III 中国渔业资源配置——可复现研究包

[![Reproduce](https://github.com/niqundaye/Frontiers-in-Marine-Science/actions/workflows/reproduce.yml/badge.svg)](https://github.com/niqundaye/Frontiers-in-Marine-Science/actions/workflows/reproduce.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/Code%20license-MIT-green.svg)](LICENSE)

[English](README.md) · [审稿人验证指南](ARTIFACT_EVALUATION.md) ·
[数据与代码可用性](DATA_AVAILABILITY.md) ·
[实验协议](docs/EXPERIMENT_PROTOCOL.md)

## 研究包信息

本仓库对应论文：

> Liu, N., Mao, N., and Huang, J. (2026). “Optimizing sustainable fishery
> resource allocation in China: an improved adaptive NSGA-III approach under
> multi-dimensional rigid constraints.” *Frontiers in Marine Science*, 13,
> 1809036. <https://doi.org/10.3389/fmars.2026.1809036>

研究包版本为 **0.3.0**，包含代码、实验配置、经过处理的数据、官方公开数据、
已生成结果、测试、运行环境、来源记录和机器可读校验，便于审稿人独立检查。

> **复现边界：**本仓库属于透明重建和公开数据代理实验，不是作者原始运行日志的
> 严格数值复制。论文没有公开 31 省完整系数矩阵、区域 TAC、数字化指数底层输入、
> 收入/成本系数和原始 30 次运行日志。本仓库不会伪造这些材料。

## 审稿人快速验证

建议使用 Python 3.12。

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pip install --no-deps -e .
.venv\Scripts\python scripts\reviewer_quick_check.py
```

该命令无需联网，也不会修改仓库中的结果文件。它将：

1. 按 `ARTIFACT_MANIFEST.csv` 核验全部交付文件的规范化 SHA-256（文本统一 LF，
   二进制按原始字节）；
2. 以只检查模式执行包级可复现性审计；
3. 运行全部单元测试；
4. 在临时目录执行 6 次小规模优化实验；
5. 核验算法、运行次数、迭代记录、三个目标和七类约束；
6. 输出以 `"status": "pass"` 结尾的 JSON 报告。

## 可复现性声明

| 内容 | 仓库证据 | 状态 |
|---|---|---|
| 论文表 1–4 | `data/paper/`、`implementations/table_*` | 精确转录并自动校验 |
| 论文图 1–10 | `data/processed/manuscript_figures/`、`results/figures/` | 从 DOCX 直接提取，保留映射和 SHA-256 |
| 图 2–10 绘图数据 | `results/data/`、`implementations/figure_*` | 依据论文曲线和数值锚点整理的经过处理的数据 |
| 248 维 PPMS 模型 | `src/fishery_repro/model.py` | 可执行的结构复现 |
| 三种算法实验 | `src/fishery_repro/experiment.py` | 固定随机种子、显式算子、逐代日志和最终解 |
| 全国公开数据核验 | `data/public/`、`src/fishery_repro/public_data.py` | 确定性解析，保留单位、网址、日期和网页哈希 |
| 作者未公开输入及原始日志 | 论文未提供 | 明确标记为缺失，不作为作者数据进行插补 |

所有重建或新生成记录均标注为“经过处理的数据”或“公开数据代理实验”。
不得将 `results/data/` 或 `results/experiments/processed_demo/` 描述为作者原始
30 次运行日志。

## 四种运行路径

| 路径 | 命令 | 是否联网 | 用途 |
|---|---|---:|---|
| 审稿人快速检查 | `python scripts/reviewer_quick_check.py` | 否 | 完整性、测试和可执行性 |
| 完整示范重建 | `python scripts/reproduce_research_artifact.py` | 否 | 重建图、代理实验和审计 |
| 刷新官方公开数据 | `python -m fishery_repro public-data` | 是 | 重新抓取和解析官方数据 |
| 容器运行 | 构建并运行 `Dockerfile` | 构建时需要 | 在统一环境执行快速检查 |

论文尺度协议 `population=200`、`generations=1000`、每种算法 30 次独立运行，
已经写入 `configs/experiments/paper_protocol.yaml`。该配置是论文协议声明，
不代表已经恢复作者未公开的省级输入。

## 已提供的审稿证据

- 10 张论文原始组合图和 10 张代码重绘对照图；
- 4 个论文表格的精确结构化转录；
- 15 次示范实验、450 条逐代记录；
- 720 个最终种群解、三个目标和七类约束；
- 每个最终解的完整 248 维决策向量；
- 农业农村部 2024 年 99 条详细渔业数据；
- 2024 年 12 条渔业生态环境数据；
- 2025 年全国与浙江 6 条最新水产品数据；
- 包级验证报告和全仓库 SHA-256 清单。

## 仓库结构

```text
ARTIFACT_EVALUATION.md   审稿流程、运行时间和通过标准
DATA_AVAILABILITY.md     数据/代码可用性、限制与投稿声明
configs/                 论文尺度、示范和 CI 实验配置
data/paper/              论文表格精确转录
data/processed/          DOCX 原图面板及来源记录
data/public/             官方公开数据、来源目录和审阅工作簿
data/verified/           独立官方数值核验
docs/                    算法、实验协议、数据来源和限制
implementations/         每张图/表对应的代码、输入、输出和校验
results/                 图、数据、实验日志和验证报告
scripts/                 审稿检查、完整运行、下载与审计工具
src/fishery_repro/       模型、算法、数据与结果流水线
tests/                   数据、模型、元数据、绘图和集成测试
```

## 投稿前归档

`DATA_AVAILABILITY.md` 已提供适合论文使用的数据与代码可用性说明。
`CITATION.cff`、`codemeta.json` 和 `.zenodo.json` 已统一为版本 0.3.0。

GitHub `main` 分支可以继续修改，因此投稿终稿中不能只依赖可变链接。投稿前应创建
GitHub Release，并通过 Zenodo 或同类平台生成永久 DOI，再把 DOI 写入论文的
Data Availability 和 Code Availability Statement。

## 许可证

仓库代码采用 MIT 许可证。论文来源图表应按照论文 CC BY 条款署名；公开数据继续
适用各官方网站的使用条款；《中国渔业统计年鉴》未在仓库中重新分发。
