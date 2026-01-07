"""
USB报警灯控制器 + Robot Telemetry Visualization

一个基于实际USB串口通讯协议的Python库，支持控制红灯、绿灯、蓝灯，
以及通过Enter键实现颜色轮换功能。

同时提供Real-Time Robot Telemetry & Notification模块，使用Rerun SDK
进行机器人遥测数据的实时可视化。

主要功能:
- USB报警灯控制（红、绿、蓝、白、黄、青、品红）
- 颜色轮换功能
- Socket API接口
- 基于Modbus RTU协议的串口通讯
- 机器人遥测可视化（Rerun SDK）
- 内置仿真模式（无需真实机器人硬件）

示例（灯控制）:
    from dataarm_notifier import USBLampController

    controller = USBLampController(port='/dev/cu.usbserial-1330')
    controller.set_red(on=True)
    controller.start_color_cycle()
    controller.stop_color_cycle()
    controller.close()

示例（遥测）:
    from dataarm_notifier import TelemetryProducer

    producer = TelemetryProducer(app_name="Robot_Telemetry")
    producer.log_position(target, actual)
    producer.shutdown()

许可证: MIT
作者: lr-2002
版本: 1.1.0
"""

__version__ = "1.1.0"
__author__ = "lr-2002"
__email__ = "wang2629651228@gmail.com"
__license__ = "MIT"

from .usb_lamp_controller import USBLampController, LightColor
from .keyboard_listener import KeyboardListener
from .color_cycle_controller import ColorCycleController, ColorCycleConfig
from .robot_state_notifier import RobotStateNotifier, RobotState, RecordingController

# Telemetry module exports
from .telemetry import (
    TelemetryProducer,
    SimulationEngine,
    StatusLevel,
    ProfileType,
    TelemetryConfig,
    TelemetryDataPoint,
    DashboardState,
    EventLog,
    SimulationProfile,
    SimulationData,
    TelemetryThresholds,
)

__all__ = [
    # Original modules
    "USBLampController",
    "LightColor",
    "KeyboardListener",
    "ColorCycleController",
    "ColorCycleConfig",
    "RobotStateNotifier",
    "RobotState",
    "RecordingController",
    # Telemetry module
    "TelemetryProducer",
    "SimulationEngine",
    "StatusLevel",
    "ProfileType",
    "TelemetryConfig",
    "TelemetryDataPoint",
    "DashboardState",
    "EventLog",
    "SimulationProfile",
    "SimulationData",
    "TelemetryThresholds",
]
