# 248 维 PPMS-MOO 与 IA-NSGA-III 详细实现

此目录不再只是烟雾测试入口：

- `source_snapshot/model.py`：31×4×2 决策张量、三个目标、七个约束与逐步修复；
- `source_snapshot/benchmark.py`：SBX、Polynomial Mutation、参考方向和四类算法构造；
- `source_snapshot/experiment.py`：独立重复、逐代日志、参考方向移动、最终解和运行元数据；
- `processed_demo.yaml`：5 个种子、3 个算法、全部算子参数；
- `experiment_output/`：经过处理的数据，包括逐代日志、最终 248 维决策向量和统计摘要；
- `run.py`：从配置完整重跑上述实验。

这是一套公开代理模型，不是作者未公开的省级输入矩阵或原始 30 次日志。

```powershell
.venv\Scripts\python implementations/model_248d/run.py
```
