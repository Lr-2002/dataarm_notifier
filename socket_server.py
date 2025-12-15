#!/usr/bin/env python3
"""
USB报警灯Socket API服务器
提供网络API接口来控制USB报警灯
"""

import socket
import json
import threading
import time
from usb_lamp_controller import USBLampController, LightColor


class SocketServer:
    """Socket API服务器类"""

    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.controller = USBLampController()
        self.server_socket = None
        self.running = False
        self.client_threads = []

    def start(self):
        """启动服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self.running = True

        print(f"=" * 60)
        print(f"USB报警灯Socket API服务器启动成功")
        print(f"监听地址: {self.host}:{self.port}")
        print(f"=" * 60)
        print("\n支持的API命令:")
        print("  set_red on|off           - 控制红灯")
        print("  set_green on|off         - 控制绿灯")
        print("  set_blue on|off          - 控制蓝灯")
        print("  turn_off_all             - 关闭所有灯")
        print("  start_cycle [interval]   - 开始颜色轮换(默认1秒)")
        print("  stop_cycle               - 停止颜色轮换")
        print("  get_status               - 获取当前状态")
        print("  help                     - 显示帮助信息")
        print("=" * 60)

        try:
            while self.running:
                client_socket, client_address = self.server_socket.accept()
                print(f"\n[连接] 客户端连接: {client_address}")

                # 为每个客户端创建独立的线程
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                self.client_threads.append(client_thread)

        except KeyboardInterrupt:
            print("\n\n[中断] 服务器被中断")
        finally:
            self.stop()

    def stop(self):
        """停止服务器"""
        self.running = False

        # 停止颜色轮换
        if self.controller.color_cycle:
            self.controller.stop_color_cycle()

        # 关闭所有客户端连接
        for thread in self.client_threads:
            if thread.is_alive():
                # 这里无法直接关闭线程，只能等待
                pass

        if self.server_socket:
            self.server_socket.close()
            print("\n[关闭] 服务器已关闭")

    def handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        try:
            # 发送欢迎信息
            welcome_msg = {
                "status": "success",
                "message": "USB报警灯控制服务器已连接",
                "commands": ["set_red", "set_green", "set_blue", "turn_off_all",
                            "start_cycle", "stop_cycle", "get_status", "help"]
            }
            self.send_response(client_socket, welcome_msg)

            while self.running:
                # 接收数据
                data = client_socket.recv(1024).decode('utf-8').strip()

                if not data:
                    break

                print(f"[请求] {client_address}: {data}")

                try:
                    # 解析命令
                    response = self.process_command(data)
                    self.send_response(client_socket, response)

                except Exception as e:
                    error_response = {
                        "status": "error",
                        "message": f"命令执行错误: {str(e)}"
                    }
                    self.send_response(client_socket, error_response)

        except ConnectionResetError:
            print(f"[断开] 客户端断开连接: {client_address}")
        except Exception as e:
            print(f"[错误] 客户端异常 {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"[结束] 客户端会话结束: {client_address}")

    def send_response(self, client_socket, response):
        """发送响应给客户端"""
        try:
            response_data = json.dumps(response, ensure_ascii=False)
            client_socket.send(response_data.encode('utf-8') + b'\n')
        except Exception as e:
            print(f"[错误] 发送响应失败: {e}")

    def process_command(self, command):
        """处理命令"""
        parts = command.split()
        if not parts:
            return {
                "status": "error",
                "message": "空命令"
            }

        cmd = parts[0].lower()

        if cmd == "help":
            return {
                "status": "success",
                "message": "可用命令",
                "commands": {
                    "set_red on|off": "控制红灯开关",
                    "set_green on|off": "控制绿灯开关",
                    "set_blue on|off": "控制蓝灯开关",
                    "turn_off_all": "关闭所有灯",
                    "start_cycle [interval]": "开始颜色轮换(间隔秒数，默认1秒)",
                    "stop_cycle": "停止颜色轮换",
                    "get_status": "获取当前状态"
                }
            }

        elif cmd == "set_red":
            if len(parts) < 2:
                return {"status": "error", "message": "缺少参数"}
            state = parts[1].lower() == "on"
            self.controller.set_red(state)
            return {"status": "success", "message": f"红灯已{'开启' if state else '关闭'}"}

        elif cmd == "set_green":
            if len(parts) < 2:
                return {"status": "error", "message": "缺少参数"}
            state = parts[1].lower() == "on"
            self.controller.set_green(state)
            return {"status": "success", "message": f"绿灯已{'开启' if state else '关闭'}"}

        elif cmd == "set_blue":
            if len(parts) < 2:
                return {"status": "error", "message": "缺少参数"}
            state = parts[1].lower() == "on"
            self.controller.set_blue(state)
            return {"status": "success", "message": f"蓝灯已{'开启' if state else '关闭'}"}

        elif cmd == "turn_off_all":
            self.controller.turn_off_all()
            return {"status": "success", "message": "所有灯已关闭"}

        elif cmd == "start_cycle":
            interval = 1.0
            if len(parts) > 1:
                try:
                    interval = float(parts[1])
                except ValueError:
                    return {"status": "error", "message": "间隔时间必须是数字"}
            self.controller.start_color_cycle(interval)
            return {
                "status": "success",
                "message": f"颜色轮换已开始，间隔{interval}秒"
            }

        elif cmd == "stop_cycle":
            self.controller.stop_color_cycle()
            return {"status": "success", "message": "颜色轮换已停止"}

        elif cmd == "get_status":
            status = self.controller.get_status()
            return {
                "status": "success",
                "message": "当前状态",
                "data": status
            }

        else:
            return {
                "status": "error",
                "message": f"未知命令: {cmd}"
            }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='USB报警灯Socket API服务器')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8888, help='监听端口 (默认: 8888)')

    args = parser.parse_args()

    server = SocketServer(host=args.host, port=args.port)
    server.start()


if __name__ == "__main__":
    main()
