#!/usr/bin/env python3
"""
USB报警灯控制器 - 使用示例

演示如何使用usb-alarm-light包控制报警灯
"""

from dataarm_notifier import USBLampController
import time


def example_basic_control():
    """基础控制示例"""
    print("=" * 60)
    print("示例1: 基础灯光控制")
    print("=" * 60)

    # 创建控制器实例
    controller = USBLampController(port='/dev/cu.usbserial-1330')

    print("\n1. 开启红灯")
    controller.set_red(on=True)
    time.sleep(1)

    print("\n2. 开启绿灯")
    controller.set_green(on=True)
    time.sleep(1)

    print("\n3. 开启蓝灯")
    controller.set_blue(on=True)
    time.sleep(1)

    print("\n4. 关闭所有灯")
    controller.turn_off_all()

    controller.close()


def example_brightness_control():
    """亮度控制示例"""
    print("\n" + "=" * 60)
    print("示例2: 亮度控制")
    print("=" * 60)

    controller = USBLampController(port='/dev/cu.usbserial-1330')

    brightness_levels = [100, 75, 50, 25, 0]

    for level in brightness_levels:
        print(f"\n设置红灯亮度: {level}%")
        controller.set_red(on=True, brightness=level)
        time.sleep(0.5)

    controller.turn_off_all()
    controller.close()


def example_color_cycle():
    """颜色轮换示例"""
    print("\n" + "=" * 60)
    print("示例3: 颜色轮换")
    print("=" * 60)

    controller = USBLampController(port='/dev/cu.usbserial-1330')

    print("\n开始颜色轮换 (间隔2秒)...")
    controller.start_color_cycle()

    print("\n等待5秒...")
    time.sleep(5)

    print("\n停止颜色轮换")
    controller.stop_color_cycle()

    controller.close()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("USB报警灯控制器 - 使用示例")
    print("=" * 60)
    print("\n设备: /dev/cu.usbserial-1330")
    print("波特率: 4800")
    print("=" * 60)

    while True:
        print("\n请选择要运行的示例:")
        print("1. 基础灯光控制")
        print("2. 亮度控制")
        print("3. 颜色轮换")
        print("0. 退出")

        choice = input("\n请输入选择 (0-3): ").strip()

        if choice == '0':
            print("\n程序退出")
            break
        elif choice == '1':
            example_basic_control()
        elif choice == '2':
            example_brightness_control()
        elif choice == '3':
            example_color_cycle()
        else:
            print("\n无效选择，请重新输入")


if __name__ == "__main__":
    main()
