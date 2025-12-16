# USB报警灯控制器

[![PyPI version](https://badge.fury.io/py/dataarm-notifier.svg)](https://badge.fury.io/py/dataarm-notifier)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个基于实际USB串口通讯协议的Python库，支持控制红灯、绿灯、蓝灯，以及通过Enter键实现颜色轮换功能。

## 特性

- ✅ 控制三种颜色的灯（红、绿、蓝）
- ✅ 支持PWM调光（0-100%亮度控制）
- ✅ 颜色轮换功能（默认2秒间隔）
- ✅ Socket API接口
- ✅ 基于Modbus RTU协议的串口通讯
- ✅ 跨平台支持（Windows、Linux、macOS）

## 安装

```bash
pip install dataarm-notifier
```

## 快速开始

```python
from dataarm_notifier import USBLampController
import time

# 创建控制器实例
controller = USBLampController(port='/dev/cu.usbserial-1330')

# 控制灯光
controller.set_red(on=True)      # 开启红灯
time.sleep(1)
controller.set_green(on=True)    # 开启绿灯
time.sleep(1)
controller.set_blue(on=True)     # 开启蓝灯
time.sleep(1)

# 颜色轮换
controller.start_color_cycle()   # 开始轮换
time.sleep(5)
controller.stop_color_cycle()    # 停止轮换

# 关闭所有灯
controller.turn_off_all()
controller.close()
```

## 命令行工具

安装包后会提供三个命令行工具：

```bash
# 直接运行控制器
usb-lamp

# 启动Socket服务器
usb-lamp-server

# 启动Socket客户端
usb-lamp-client
```

## 设备路径

根据你的操作系统和设备，修改串口路径：

- **Linux**: `/dev/ttyUSB0` 或 `/dev/ttyACM0`
- **macOS**: `/dev/cu.usbserial-1330`
- **Windows**: `COM3` 或 `COM4`

## 示例

查看完整示例：

```bash
python -c "from usb_alarm_light import example; example.main()"
```

## 文档

- [完整文档](https://github.com/yourusername/usb-alarm-light#readme)
- [开发指南](https://github.com/yourusername/usb-alarm-light/blob/main/DEVELOPMENT.md)

## 依赖

- Python 3.6+
- pyserial >= 3.5

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

Your Name - your.email@example.com

## 贡献

欢迎贡献！请阅读 [DEVELOPMENT.md](DEVELOPMENT.md) 了解详情。

## 问题反馈

如果你遇到问题，请在 [GitHub Issues](https://github.com/yourusername/usb-alarm-light/issues) 中报告。
