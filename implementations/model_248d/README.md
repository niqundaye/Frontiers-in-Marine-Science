# 248 维 PPMS 模型实现包

- `run.py`：IA-NSGA-III 代理实现与 NSGA 基线的烟雾基准入口；
- `smoke_summary.csv`：当前结果；
- [`src/fishery_repro/model.py`](../../src/fishery_repro/model.py)：31×4×2 决策变量、三目标和七类约束；
- [`src/fishery_repro/benchmark.py`](../../src/fishery_repro/benchmark.py)：算法和评价指标实现。

```powershell
python implementations/model_248d/run.py
```

这是可公开运行的结构代理模型；未公开省级系数没有被伪装成作者数据。
