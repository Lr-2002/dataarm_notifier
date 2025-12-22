#!/usr/bin/env python3
"""
USB报警灯控制器
支持独立控制红灯、绿灯、蓝灯，以及颜色轮换功能
基于实际USB串口通讯协议
"""

import os
import sys
import time
import threading
from enum import Enum


class LightColor(Enum):
    """灯光颜色枚举"""
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    WHITE = "white"
    YELLOW = "yellow"      # R+G
    CYAN = "cyan"          # G+B
    MAGENTA = "magenta"    # R+B
    OFF = "off"


class USBLampController:
    """USB报警灯控制器类

    基于实际协议：
    - 波特率：4800
    - 数据格式：8位，无校验，2位停止位
    - 地址码：0x01
    - 功能码：0x06 (写单个寄存器)
    - 寄存器地址：
      * 红灯：0x0008
      * 绿灯：0x0003
      * 蓝灯：0x0002
      * 白灯：0x0001
      * 灯光开关：0x0004
    - PWM值：1999为100%
    """

    def __init__(self, port='/dev/ttyUSB1', baudrate=4800):
        self.port = port
        self.baudrate = baudrate
        self.red_on = False
        self.green_on = False
        self.blue_on = False
        self.white_on = False
        self.color_cycle = False
        self.cycle_thread = None
        self.current_color_index = 0
        self.colors = [LightColor.RED, LightColor.GREEN, LightColor.BLUE]
        self.serial_conn = None

        # 寄存器地址映射
        self.register_map = {
            LightColor.RED: 0x0008,
            LightColor.GREEN: 0x0003,
            LightColor.BLUE: 0x0002,
            LightColor.WHITE: 0x0001,
        }

        # 默认PWM值（100%亮度）
        self.default_pwm = 1999

    def _crc16(self, data):
        """计算CRC16校验码"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        # 返回小端序（低字节在前，高字节在后）
        return bytes([crc & 0xFF, (crc >> 8) & 0xFF])

    def _build_command(self, register_addr, value):
        """构建完整的Modbus命令

        Args:
            register_addr: 寄存器地址 (2字节)
            value: 寄存器值 (2字节)

        Returns:
            完整的命令字节串
        """
        # 地址码 (1字节)
        addr = 0x01

        # 功能码 (1字节) - 写单个寄存器
        func_code = 0x06

        # 寄存器地址 (2字节)
        reg_high = (register_addr >> 8) & 0xFF
        reg_low = register_addr & 0xFF

        # 寄存器数据 (2字节)
        val_high = (value >> 8) & 0xFF
        val_low = value & 0xFF

        # 构建命令（不含CRC）
        cmd_without_crc = bytes([
            addr,
            func_code,
            reg_high,
            reg_low,
            val_high,
            val_low
        ])

        # 计算CRC16
        crc = self._crc16(cmd_without_crc)

        # 返回完整命令
        return cmd_without_crc + bytes([0x00, 0x00])

    def _send_command(self, command):
        """发送命令到串口设备"""
        try:
            # 尝试建立串口连接（如果尚未连接）
            if self.serial_conn is None:
                try:
                    import serial
                    self.serial_conn = serial.Serial(
                        port=self.port,
                        baudrate=self.baudrate,
                        bytesize=8,
                        parity='N',  # 无校验
                        stopbits=2,
                        timeout=1
                    )
                except ImportError:
                    return True
                except Exception:
                    return True

            # 发送命令
            self.serial_conn.write(command)
            self.serial_conn.flush()
            time.sleep(0.1)
            return True

        except Exception:
            return False

    def set_brightness(self, color, brightness=100, auto_light_on=True):
        """设置灯光亮度

        Args:
            color: 灯光颜色 (LightColor枚举)
            brightness: 亮度百分比 (0-100)
            auto_light_on: 是否自动开启灯光总开关
        """
        # 计算PWM值
        pwm_value = int(self.default_pwm * brightness / 100)

        # 限制范围
        pwm_value = max(0, min(self.default_pwm, pwm_value))

        # 如果需要开启，先发送灯光开命令
        if brightness > 0 and auto_light_on:
            self.set_light_on(True)
        # 构建并发送颜色命令
        command = self._build_command(self.register_map[color], pwm_value)
        return self._send_command(command)

    def set_light_on(self, on=True):
        """设置灯光总开关

        Args:
            on: True开启，False关闭
        """
        value = 0x0001 if on else 0x0000
        command = self._build_command(0x0004, value)

        # 发送命令
        return self._send_command(command)

    def set_red(self, on=True, brightness=100):
        """设置红灯状态"""
        self.red_on = on
        if on:
            self.turn_off_all()
            self.set_light_on(True)
            self._set_color_brightness(LightColor.RED, brightness)
        else:
            self._set_color_brightness(LightColor.RED, 0)

    def set_green(self, on=True, brightness=100):
        """设置绿灯状态"""
        self.green_on = on
        if on:
            self.turn_off_all()
            self.set_light_on(True)
            self._set_color_brightness(LightColor.GREEN, brightness)
        else:
            self._set_color_brightness(LightColor.GREEN, 0)

    def set_blue(self, on=True, brightness=100):
        """设置蓝灯状态"""
        self.blue_on = on
        if on:
            self.turn_off_all()
            self.set_light_on(True)
            self._set_color_brightness(LightColor.BLUE, brightness)
        else:
            self._set_color_brightness(LightColor.BLUE, 0)

    def set_white(self, on=True, brightness=100):
        """设置白灯状态"""
        self.white_on = on
        if on:
            self.turn_off_all()
            self.set_light_on(True)
            self._set_color_brightness(LightColor.WHITE, brightness)
        else:
            self._set_color_brightness(LightColor.WHITE, 0)

    def set_yellow(self, on=True, brightness=100):
        """设置黄灯状态 (R+G)"""
        if on:
            self.turn_off_all()
            self._set_color_brightness(LightColor.RED, brightness)
            self._set_color_brightness(LightColor.GREEN, brightness)

            self.set_light_on(True)
            self.red_on = True
            self.green_on = True
        else:
            self._set_color_brightness(LightColor.RED, 0)
            self._set_color_brightness(LightColor.GREEN, 0)
            self.red_on = False
            self.green_on = False

    def set_cyan(self, on=True, brightness=50):
        """设置青色灯状态 (G+B)"""
        if on:
            self.turn_off_all()
            self.set_light_on(True)
            self._set_color_brightness(LightColor.GREEN, brightness)
            self._set_color_brightness(LightColor.BLUE, brightness)
            self.green_on = True
            self.blue_on = True
        else:
            self._set_color_brightness(LightColor.GREEN, 0)
            self._set_color_brightness(LightColor.BLUE, 0)
            self.green_on = False
            self.blue_on = False

    def set_magenta(self, on=True, brightness=100):
        """设置品红灯状态 (R+B)"""
        if on:
            self.turn_off_all()
            self.set_light_on(True)
            self._set_color_brightness(LightColor.RED, brightness)
            self._set_color_brightness(LightColor.BLUE, brightness)
            self.red_on = True
            self.blue_on = True
        else:
            self._set_color_brightness(LightColor.RED, 0)
            self._set_color_brightness(LightColor.BLUE, 0)
            self.red_on = False
            self.blue_on = False

    def _set_color_brightness(self, color, brightness=100):
        """内部方法：仅设置颜色亮度（不控制总开关）"""
        # 计算PWM值
        pwm_value = int(self.default_pwm * brightness / 100)

        # 限制范围
        pwm_value = max(0, min(self.default_pwm, pwm_value))

        # 构建并发送颜色命令
        command = self._build_command(self.register_map[color], pwm_value)
        time.sleep(0.1)
        return self._send_command(command)

    def turn_off_all(self):
        """关闭所有灯"""
        self.red_on = False
        self.green_on = False
        self.blue_on = False
        self.white_on = False

        self._set_color_brightness(LightColor.RED, 0)
        self._set_color_brightness(LightColor.GREEN, 0)
        self._set_color_brightness(LightColor.BLUE, 0)
        self._set_color_brightness(LightColor.WHITE, 0)

    def start_color_cycle(self, interval=2.0):
        """开始颜色轮换"""
        if self.color_cycle:
            return

        self.color_cycle = True
        self.current_color_index = 0
        self.cycle_thread = threading.Thread(
            target=self._cycle_colors,
            args=(interval,),
            daemon=True
        )
        self.cycle_thread.start()

    def stop_color_cycle(self):
        """停止颜色轮换"""
        self.color_cycle = False
        if self.cycle_thread:
            self.cycle_thread.join(timeout=1.0)
        self.turn_off_all()

    def _cycle_colors(self, interval):
        """颜色轮换循环

        严格按照以下顺序执行：
        1. 关掉灯 - 关闭所有灯（设置所有颜色亮度为0）
        2. 打开灯开关 - 发送灯光开命令
        3. 调整到目标灯的数值亮度 - 设置目标颜色亮度
        """
        while self.color_cycle:
            # 步骤1: 关掉灯 - 关闭所有灯
            self._set_color_brightness(LightColor.RED, 0)
            self._set_color_brightness(LightColor.GREEN, 0)
            self._set_color_brightness(LightColor.BLUE, 0)
            self._set_color_brightness(LightColor.WHITE, 0)
            time.sleep(0.1)

            # 步骤2: 打开灯开关
            self.set_light_on(True)

            # 步骤3: 调整到目标灯的数值亮度
            current_color = self.colors[self.current_color_index]
            if current_color == LightColor.RED:
                self._set_color_brightness(LightColor.RED, 100)
            elif current_color == LightColor.GREEN:
                self._set_color_brightness(LightColor.GREEN, 100)
            elif current_color == LightColor.BLUE:
                self._set_color_brightness(LightColor.BLUE, 100)

            # 移动到下一个颜色
            self.current_color_index = (self.current_color_index + 1) % len(self.colors)

            # 等待指定间隔
            time.sleep(interval)

    def get_status(self):
        """获取当前状态"""
        return {
            "red": self.red_on,
            "green": self.green_on,
            "blue": self.blue_on,
            "white": self.white_on,
            "color_cycle": self.color_cycle,
            "current_color": self.colors[self.current_color_index].value if self.color_cycle else None
        }

    def close(self):
        """关闭串口连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()


def main():
    """主函数 - 演示颜色轮换功能"""
    import argparse

    parser = argparse.ArgumentParser(description='USB报警灯控制器')
    parser.add_argument('--port', default='/dev/cu.usbserial-1330', help='串口设备路径 (默认: /dev/cu.usbserial-1330)')
    parser.add_argument('--baudrate', type=int, default=4800, help='波特率 (默认: 4800)')

    args = parser.parse_args()

    controller = USBLampController(port=args.port, baudrate=args.baudrate)

    print("=" * 60)
    print("USB报警灯控制器测试")
    print("=" * 60)
    print(f"\n串口配置:")
    print(f"  端口: {args.port}")
    print(f"  波特率: {args.baudrate}")
    print("\n功能说明：")
    print("1. 独立控制红灯、绿灯、蓝灯、白灯")
    print("2. 按回车键开始/停止颜色轮换")
    print("3. 输入 'quit' 退出程序")
    print("=" * 60)

    try:
        while True:
            user_input = input("\n按回车开始颜色轮换 (或输入 'quit' 退出): ").strip()

            if user_input.lower() == 'quit':
                controller.stop_color_cycle()
                controller.close()
                print("程序退出")
                break

            if not controller.color_cycle:
                print("\n开始颜色轮换...")
                controller.start_color_cycle(interval=2.0)
            else:
                print("\n停止颜色轮换...")
                controller.stop_color_cycle()

    except KeyboardInterrupt:
        print("\n\n程序被中断")
        controller.stop_color_cycle()
        controller.close()
    except Exception as e:
        print(f"\n错误: {e}")
        controller.stop_color_cycle()
        controller.close()


if __name__ == "__main__":
    main()
