"""
USB报警灯控制器

一个基于实际USB串口通讯协议的Python库，支持控制红灯、绿灯、蓝灯，
以及通过Enter键实现颜色轮换功能。

主要功能:
- 控制三种颜色的灯（红、绿、蓝）
- 颜色轮换功能
- Socket API接口
- 基于Modbus RTU协议的串口通讯

示例:
    from dataarm_notifier import USBLampController

    controller = USBLampController(port='/dev/cu.usbserial-1330')
    controller.set_red(on=True)
    controller.start_color_cycle()
    controller.stop_color_cycle()
    controller.close()

许可证: MIT
作者: lr-2002
版本: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "lr-2002"
__email__ = "wang2629651228@gmail.com"
__license__ = "MIT"

from .usb_lamp_controller import USBLampController, LightColor
from .keyboard_listener import KeyboardListener
from .color_cycle_controller import ColorCycleController, ColorCycleConfig
from .robot_state_notifier import RobotStateNotifier, RobotState, RecordingController

__all__ = [
    "USBLampController",
    "LightColor",
    "KeyboardListener",
    "ColorCycleController",
    "ColorCycleConfig",
    "RobotStateNotifier",
    "RobotState",
    "RecordingController",
]
