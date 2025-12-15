#!/usr/bin/env python3
"""
USB报警灯演示程序
演示按Enter键实现颜色轮换功能
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from usb_lamp_controller import USBLampController


def demo_individual_colors():
    """演示独立控制不同颜色的灯"""
    controller = USBLampController()

    print("=" * 60)
    print("演示1: 独立控制不同颜色的灯")
    print("=" * 60)

    # 测试红灯
    print("\n1. 开启红灯")
    controller.set_red(True)
    input("   按回车继续...")
    controller.set_red(False)

    # 测试绿灯
    print("\n2. 开启绿灯")
    controller.set_green(True)
    input("   按回车继续...")
    controller.set_green(False)

    # 测试蓝灯
    print("\n3. 开启蓝灯")
    controller.set_blue(True)
    input("   按回车继续...")
    controller.set_blue(False)

    # 测试组合颜色
    print("\n4. 测试组合颜色 (红+绿=黄)")
    controller.set_red(True)
    controller.set_green(True)
    input("   按回车继续...")

    print("\n5. 测试组合颜色 (红+蓝=紫)")
    controller.set_red(True)
    controller.set_blue(True)
    input("   按回车继续...")

    print("\n6. 测试组合颜色 (绿+蓝=青)")
    controller.set_green(True)
    controller.set_blue(True)
    input("   按回车继续...")

    print("\n7. 测试组合颜色 (红+绿+蓝=白)")
    controller.set_red(True)
    controller.set_green(True)
    controller.set_blue(True)
    input("   按回车继续...")

    # 关闭所有灯
    print("\n8. 关闭所有灯")
    controller.turn_off_all()

    print("\n" + "=" * 60)
    print("演示1完成")
    print("=" * 60)


def demo_color_cycle():
    """演示按Enter键实现颜色轮换"""
    controller = USBLampController()

    print("\n" + "=" * 60)
    print("演示2: 按Enter键实现颜色轮换")
    print("=" * 60)
    print("\n说明:")
    print("- 首次按回车: 开始颜色轮换 (红→绿→蓝→红...)")
    print("- 再次按回车: 停止颜色轮换")
    print("- 输入 'quit': 退出程序")
    print("=" * 60)

    try:
        while True:
            user_input = input("\n按回车开始颜色轮换 (或输入 'quit' 退出): ").strip()

            if user_input.lower() == 'quit':
                print("\n程序退出")
                break

            if not controller.color_cycle:
                print("\n>>> 开始颜色轮换...")
                print("    颜色顺序: 红 → 绿 → 蓝 → 红 → ...")
                controller.start_color_cycle(interval=2.0)
            else:
                print("\n>>> 停止颜色轮换...")
                controller.stop_color_cycle()

    except KeyboardInterrupt:
        print("\n\n程序被中断")
        controller.stop_color_cycle()
    except Exception as e:
        print(f"\n错误: {e}")
        controller.stop_color_cycle()

    print("\n" + "=" * 60)
    print("演示2完成")
    print("=" * 60)


def demo_status():
    """演示状态查询"""
    controller = USBLampController()

    print("\n" + "=" * 60)
    print("演示3: 状态查询")
    print("=" * 60)

    # 获取初始状态
    print("\n初始状态:")
    status = controller.get_status()
    print(f"  红灯: {status['red']}")
    print(f"  绿灯: {status['green']}")
    print(f"  蓝灯: {status['blue']}")

    # 开启红灯
    controller.set_red(True)
    status = controller.get_status()
    print("\n开启红灯后:")
    print(f"  红灯: {status['red']}")
    print(f"  绿灯: {status['green']}")
    print(f"  蓝灯: {status['blue']}")

    # 开始颜色轮换
    controller.start_color_cycle(0.5)
    input("\n按回车查看颜色轮换状态...")
    status = controller.get_status()
    print("\n颜色轮换时:")
    print(f"  红灯: {status['red']}")
    print(f"  绿灯: {status['green']}")
    print(f"  蓝灯: {status['blue']}")
    print(f"  颜色轮换: {status['color_cycle']}")
    if status['current_color']:
        print(f"  当前颜色: {status['current_color']}")

    controller.stop_color_cycle()
    controller.turn_off_all()

    print("\n" + "=" * 60)
    print("演示3完成")
    print("=" * 60)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("USB报警灯控制演示程序")
    print("=" * 60)

    while True:
        print("\n请选择演示功能:")
        print("1. 演示独立控制不同颜色的灯")
        print("2. 演示按Enter键实现颜色轮换")
        print("3. 演示状态查询")
        print("4. 退出")

        choice = input("\n请输入选择 (1-4): ").strip()

        if choice == '1':
            demo_individual_colors()
        elif choice == '2':
            demo_color_cycle()
        elif choice == '3':
            demo_status()
        elif choice == '4':
            print("\n程序退出")
            break
        else:
            print("\n无效选择，请重新输入")


if __name__ == "__main__":
    main()
