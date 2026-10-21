# 来源与第三方许可

## 新增部分

本次新增的 `visionprep/`、`tests/`、`tools/`、原创工程 SVG、合成样例及原创说明适用根目录 MIT。MIT 不改变下面第三方内容的许可。

## 培训基线和任务书

来源为提供者确认获准公开的 2026 年 6 月《培训任务书》及“基线程序”。提供者已明确要求保留原始来源署名。原资料未给出详细著作权人和统一开源许可证，因此原基线、任务书转录、原始插图与从其内部提取的标定板/PCB图像不自动适用新增部分的 MIT；进一步使用应遵守原权利条件。

`reference/visionplus/` 保留原工程和原始字节；`docs/taskbook-transcript.md`、`docs/images/source/taskbook-*.png` 保留任务内容；`training-reference-*.png` 是从获准公开的原基线内提取的全幅图像。来源、像素和文件哈希均有清单。

VisionPlus / V+、DCCK 标识及平台格式属于其权利方。保留标识用于说明原环境与来源，不表示厂商为本项目背书。本项目不分发商业平台安装程序、厂商 DLL、账户库、授权加密狗配置或工程保护材料。

## 外部参考照片

1. **SVCam-ECO Series black with Tubus.JPG**，作者 Alexander Lucke，经 Wikimedia Commons 提供，许可证 [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)。[原说明页](https://commons.wikimedia.org/wiki/File:SVCam-ECO_Series_black_with_Tubus.JPG)。仓库文件 `docs/images/reference/camera-reference.jpg` 保持上游当前版本原始字节，未作编辑；该照片本身继续适用 CC BY-SA 3.0。
2. **KUKA Industrial Robot KR10 SCARA.jpg**，摄影 Jo Teichmann，为 KUKA Roboter GmbH 制作。权利方已按原页声明释放为公有领域。[原说明页](https://commons.wikimedia.org/wiki/File:KUKA_Industrial_Robot_KR10_SCARA.jpg)。仓库文件 `docs/images/reference/robot-reference.jpg` 保持原字节，未作编辑。

这两张照片只作外形/设备类别参考，未认定为本培训所用型号或作者拥有的器材；未拼接后改称实物组装照片。来源与上游许可元数据见 `manifests/external-images.json`。

## 合成内容

`examples/demo/` 内 PCB 输入和九点坐标由程序生成，结果为该程序对合成输入的实际计算。`docs/images/station-blueprint.svg` 等图解是工程说明，`offline-results.png` 是结果汇总绘图。它们不是实物照片、相机实采数据或原 VisionPlus HMI 的运行截图。
