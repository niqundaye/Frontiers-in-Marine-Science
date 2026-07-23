# 图 4 独立实现包

证据等级：**校准重建：三目标 KPI 雷达图**。

## 文件

- `run.py`：本图独立运行入口；
- `input_data.csv`：本图实际读取的数据。
- `Figure_04_kpi_radar.png` / `.svg`：当前生成结果；
- 共享核心实现：[`src/fishery_repro/figures.py`](../../src/fishery_repro/figures.py)。

## 运行

在仓库根目录完成 `pip install -e .` 后：

```powershell
python implementations/figure_04/run.py
```

图 2-10 的输入数据是论文锚点约束下的确定性校准重建，不是作者原始 30 次运行日志。
