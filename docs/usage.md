# 运行与配置

## 离线演示

安装 `requirements.txt`，在项目根目录执行 `python -m visionprep demo --output output/run-01`。目录必须不存在或为空。程序会生成六类合成 PCB 图像，执行检测，计算九点平面映射并生成运动字符串，然后保存结果。

生成的 `index.html` 可直接用浏览器打开；页面不需要网络或外部前端依赖。它展示软件的实际输出，顶部明确标注合成输入和离线模式。程序不会在执行演示时创建相机、串口或 PLC 网络连接。

输出包括 `SourceImage_时间戳_样例名.png`、`RecordImage_时间戳_样例名.png`、逐样例 JSON、`results.synthetic.csv`、`summary.synthetic.json`、`user-log.jsonl` 和标定输入/拟合结果。提交的示例位于 `examples/demo/`，其数值是实际运行生成，并非手工填写的实测结果。

## 光学选型

```powershell
python -m visionprep optics
```

讲解例题：传感器横向 6.4 mm、WD 400 mm、视野横向 160 mm，按任务书近似公式得到 f=16 mm。

练习：WD=150 mm、视野至少 16×12 mm。横向限制 f≤60 mm，纵向限制 f≤57.5 mm，应同时满足两个方向。以标准 50 mm 作为课内计算示例，得到 19.2×13.8 mm 视野；60 mm 的纵向视野只有 11.5 mm，不满足题目。

这些是任务书模型下的计算值。实际镜头还要检查最近对焦、接口、成像圈、工作距离定义、畸变及真实拍摄视野；没有凭公式指定已购器件或保证其在近距离可用。

## 拟合平面坐标映射

```powershell
python -m visionprep calibrate --points examples/demo/calibration.synthetic.json --output output/calibration-fit.json
```

输入为成对的 `pixels` 和 `robot_xy_mm`，至少三对非共线有限点。随附九点文件带 `is_synthetic: true`。返回 2×3 仿射矩阵及拟合残差；这不是三维眼在手上/眼在手外标定，也不是独立量测精度证明。

## 检测其他图像

```powershell
python -m visionprep inspect --image path/to/image.png --config examples/demo/roi.synthetic.json --output output/inspection-01
```

示例 ROI 仅适用于已配准的 960×640 合成布局。程序拒绝分辨率不一致、空 ROI 和越界 ROI。真实图像应先定位到参考姿态，并根据实际器件位置修改配置与阈值；不要把随附坐标当作真实 PCB 的通用参数。

## 查看原 VisionPlus 基线

原工程位于 `reference/visionplus/基线程序.vpsx`。需要独立安装并授权商业平台。为查看而创建一个关闭采图与写设备节点的新副本：

```powershell
python tools/prepare_baseline.py --destination runtime-inspection
```

此命令仅创建查看副本，不补齐原本缺失的相机/PLC设备、HMI或主流程算法节点。需要实际联调时，先阅读 [硬件接入说明](commissioning.md)。原基线中的运动坐标属于培训历史数据，不能直接视为当前机器的坐标和行程。
