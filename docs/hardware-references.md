# 硬件参考与选型条件

工程图采用自行绘制的器件轮廓和模块关系，外部照片单独陈列。它们说明相机、光学、PLC 和取放机构的角色，不是作者已经拥有或组装完成的设备清单。

| 模块 | 任务/设计条件 | 型号状态 |
|---|---|---|
| 工业相机 | 颜色检测需要彩色输入，固定曝光后采集；IP 按任务书 | 原基线未保存相机配置，实际型号待确认 |
| 镜头 | 与相机接口、成像圈、真实视野、最短物距匹配 | 50 mm 只作任务书近似计算示例 |
| 环形光与控制器 | 稳定照明；控制器 19200 bps、COM1/COM2 | 接口电平、电源和命令帧需按器件手册确认 |
| PLC | 任务指定汇川 H5U，TCP 端口 502 | 官方支持 Modbus TCP 与 Socket；PLC 程序待提供 |
| 机械手 | 四轴坐标与吸吹气指令来自任务书 | 具体机构型号、行程和回包未给出 |
| 真空吸嘴/气泵 | 用于取放；与控制器和供电配套 | 选型、气路和电源按实际铭牌 |
| 工控机/网络 | 运行视觉平台或新增离线参考程序 | IP 参数是实验配置，不自动改写本机设置 |

参考来源：

- [汇川 H5U 官方产品资料](https://www.inovance.com/global/content/details_815_403258.html)：用于核对 PLC 接口能力。
- [Computar 近距离镜头示例资料](https://www.computar.com/products/v5040-mpz-r)：说明最短物距也是镜头选型条件；该页面标明产品已停产，本项目没有将其列为采购推荐。
- [SVCam-ECO 原照片与许可](https://commons.wikimedia.org/wiki/File:SVCam-ECO_Series_black_with_Tubus.JPG)：工业相机外观参考，非本系统已选型号。
- [KUKA 机器人原照片与许可](https://commons.wikimedia.org/wiki/File:KUKA_Industrial_Robot_KR10_SCARA.jpg)：机构外观参考，非本培训机械手的实物照片或已匹配的型号。

所有原照片保持下载字节不变。许可证与作者见 [第三方说明](../THIRD_PARTY_NOTICES.md) 和 `manifests/external-images.json`。
