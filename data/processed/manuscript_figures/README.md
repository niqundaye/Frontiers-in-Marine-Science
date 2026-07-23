# 论文原图提取：经过处理的数据

本目录保存从用户提供的 `316Manuscript.DOCX` 中直接提取的 20 张内嵌图片，映射到论文图 1–10。数据标识统一为：**经过处理的数据**。

- `panels/`：从 DOCX 的 OOXML 媒体目录直接提取的单图或子图，像素内容未改动；
- `manifest.csv`：论文图号、子图号、DOCX 内部媒体路径、尺寸和 SHA-256；
- `results/figures/*.png`：使用这些子图排版得到的主要实验结果图；
- `results/processed_data_replots/`：代码根据结构化 CSV 生成的可复查结果，不作为 DOCX 原图。

多子图结果只进行白底排版和 `(a)/(b)/(c)` 标注，没有重新拟合或修改曲线数值。来源 DOCX 的 SHA-256 为：

`2ee3d23f1a5592b59e6c3e190bc361e1fdb4024405d7a8c5e2681fc3575bb2e0`

重新导入：

```powershell
python scripts/import_manuscript_figures.py "F:\path\to\316Manuscript.DOCX"
```
