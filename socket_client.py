#!/usr/bin/env python3
"""
USB报警灯Socket客户端
用于测试Socket API服务器
"""

import socket
import json
import sys


class SocketClient:
    """Socket客户端类"""

    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"已连接到服务器 {self.host}:{self.port}")

            # 接收欢迎信息
            response = self.receive_response()
            if response:
                print(f"服务器响应: {json.dumps(response, ensure_ascii=False, indent=2)}")

            return True

        except ConnectionRefusedError:
            print(f"错误: 无法连接到服务器 {self.host}:{self.port}")
            return False
        except Exception as e:
            print(f"连接错误: {e}")
            return False

    def send_command(self, command):
        """发送命令到服务器"""
        try:
            self.socket.send(command.encode('utf-8'))
            response = self.receive_response()
            return response

        except Exception as e:
            print(f"发送命令失败: {e}")
            return None

    def receive_response(self):
        """接收服务器响应"""
        try:
            data = self.socket.recv(4096).decode('utf-8')
            if data:
                return json.loads(data)
            return None

        except Exception as e:
            print(f"接收响应失败: {e}")
            return None

    def close(self):
        """关闭连接"""
        if self.socket:
            self.socket.close()
            print("连接已关闭")


def interactive_mode(client):
    """交互模式"""
    print("\n" + "=" * 60)
    print("USB报警灯控制客户端 - 交互模式")
    print("=" * 60)
    print("\n可用命令:")
    print("  set_red on|off")
    print("  set_green on|off")
    print("  set_blue on|off")
    print("  turn_off_all")
    print("  start_cycle [interval]")
    print("  stop_cycle")
    print("  get_status")
    print("  help")
    print("  quit")
    print("=" * 60)

    while True:
        try:
            command = input("\n请输入命令: ").strip()

            if not command:
                continue

            if command.lower() == 'quit':
                break

            response = client.send_command(command)
            if response:
                print(f"\n响应: {json.dumps(response, ensure_ascii=False, indent=2)}")

        except KeyboardInterrupt:
            print("\n\n程序被中断")
            break
        except Exception as e:
            print(f"错误: {e}")


def batch_mode(client, commands):
    """批量模式"""
    print("\n" + "=" * 60)
    print("USB报警灯控制客户端 - 批量模式")
    print("=" * 60)

    for command in commands:
        print(f"\n执行命令: {command}")
        response = client.send_command(command)
        if response:
            print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}")
        time.sleep(0.5)


def main():
    """主函数"""
    import argparse
    import time

    parser = argparse.ArgumentParser(description='USB报警灯Socket客户端')
    parser.add_argument('--host', default='localhost', help='服务器地址 (默认: localhost)')
    parser.add_argument('--port', type=int, default=8888, help='服务器端口 (默认: 8888)')
    parser.add_argument('--command', help='执行单个命令')
    parser.add_argument('--file', help='批量执行命令文件 (每行一个命令)')

    args = parser.parse_args()

    client = SocketClient(host=args.host, port=args.port)

    if not client.connect():
        sys.exit(1)

    try:
        if args.command:
            # 单命令模式
            print(f"\n执行命令: {args.command}")
            response = client.send_command(args.command)
            if response:
                print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}")

        elif args.file:
            # 批量模式
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    commands = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                batch_mode(client, commands)
            except FileNotFoundError:
                print(f"错误: 文件未找到 {args.file}")
            except Exception as e:
                print(f"读取文件错误: {e}")

        else:
            # 交互模式
            interactive_mode(client)

    finally:
        client.close()


if __name__ == "__main__":
    main()
