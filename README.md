# USB报警灯控制器

一个基于实际USB串口通讯协议的Python程序，支持独立控制红灯、绿灯、蓝灯、白灯，以及通过Enter键实现颜色轮换功能。

## 功能特性

1. **独立控制不同颜色的灯**
   - 支持单独控制红灯、绿灯、蓝灯、白灯
   - 支持PWM调光（0-100%亮度控制）
   - 支持组合颜色（红+绿=黄，红+蓝=紫，绿+蓝=青，红+绿+蓝=白等）
   - 支持一键关闭所有灯

2. **颜色轮换功能**
   - 按Enter键开始/停止颜色轮换
   - 可自定义轮换间隔时间
   - 默认轮换顺序：红 → 绿 → 蓝 → 红...
   - 多线程实现，响应迅速

3. **Socket API接口**
   - 提供网络API接口
   - 支持多客户端同时连接
   - 完整的JSON响应格式

4. **实际协议支持**
   - 基于Modbus RTU协议的串口通讯
   - 波特率：4800
   - 数据格式：8位，无校验，2位停止位
   - 标准CRC16校验

## 项目结构

```
simple_notifier/
├── usb_lamp_controller.py    # USB报警灯控制器核心模块
├── socket_server.py          # Socket API服务器
├── socket_client.py          # Socket客户端测试工具
├── demo.py                   # 演示程序
├── test.py                   # 功能测试脚本
├── test_protocol.py          # 协议测试脚本
├── requirements.txt          # Python依赖包
└── README.md                 # 说明文档
```

## 协议说明

本程序基于实际USB报警灯的串口通讯协议实现，具体参数如下：

### 电气参数
- **产品型号**: USB报警灯
- **额定电压**: 5V
- **控制方式**: USB串口通讯
- **报警颜色**: 红色、黄色、绿色、白色、蓝色
- **闪烁方式**: PWM调光

### 串口参数
- **波特率**: 4800
- **数据位**: 8位
- **校验位**: 无校验
- **停止位**: 2位

### 通讯格式 (Modbus RTU)
```
地址码 (1字节) + 功能码 (1字节) + 寄存器地址 (2字节) + 寄存器数据 (2字节) + CRC16校验 (2字节)
```

**字段说明:**
- **地址码**: 设备地址，默认 `0x01`
- **功能码**: `0x06` (写单个寄存器)
- **寄存器地址**: 见下表
- **寄存器数据**: PWM值，1999为100%亮度
- **CRC16**: 标准CRC16-MODBUS校验码

### 寄存器地址表
| 地址 | 功能 | 说明 |
|------|------|------|
| 0x0001 | 白灯 | 控制白灯亮度 |
| 0x0002 | 蓝灯 | 控制蓝灯亮度 |
| 0x0003 | 绿灯 | 控制绿灯亮度 |
| 0x0004 | 灯光开关 | 控制灯光总开关 |
| 0x0006 | 蜂鸣器开关 | 控制蜂鸣器开关 |
| 0x0008 | 红灯 | 控制红灯亮度 |

### 参考指令示例
| 指令 | 说明 |
|------|------|
| `01 06 00 04 00 01 xx xx` | 灯光开 |
| `01 06 00 04 00 00 xx xx` | 灯光关 |
| `01 06 00 08 03 E7 xx xx` | 红灯50%亮度 (999 = 0x03E7) |
| `01 06 00 03 07 CF xx xx` | 绿灯100%亮度 (1999 = 0x07CF) |
| `01 06 00 02 00 00 xx xx` | 蓝灯关闭 |
| `01 06 00 06 00 01 xx xx` | 蜂鸣器开 |

### 亮度计算
PWM值 = 1999 × (亮度百分比 / 100)

**示例:**
- 100%亮度: 1999 (0x07CF)
- 50%亮度: 999 (0x03E7)
- 25%亮度: 499 (0x01F3)
- 10%亮度: 199 (0x00C7)

## 安装说明

### 环境要求

- Python 3.6+
- pyserial (用于串口通讯)

### 安装依赖

```bash
pip install -r requirements.txt
```

或单独安装：

```bash
pip install pyserial>=3.5
```

## 使用方法

### 1. 直接控制（推荐测试）

运行演示程序，查看所有功能：

```bash
python demo.py
```

演示程序提供三个功能：
- 演示独立控制不同颜色的灯
- 演示按Enter键实现颜色轮换
- 演示状态查询

### 2. 直接运行控制器

```bash
python usb_lamp_controller.py
```

功能说明：
- 按回车键开始/停止颜色轮换
- 输入 'quit' 退出程序

### 3. Socket API服务器

启动服务器：

```bash
python socket_server.py
```

或指定IP和端口：

```bash
python socket_server.py --host 0.0.0.0 --port 8888
```

### 4. Socket客户端测试

#### 交互模式

```bash
python socket_client.py --host localhost --port 8888
```

#### 单命令模式

```bash
python socket_client.py --command "set_red on"
```

#### 批量模式

创建命令文件 `commands.txt`：

```
set_red on
set_green on
set_blue on
turn_off_all
start_cycle 0.5
stop_cycle
```

执行：

```bash
python socket_client.py --file commands.txt
```

## API命令说明

### 控制命令

| 命令 | 参数 | 说明 |
|------|------|------|
| `set_red` | on/off | 控制红灯开关 |
| `set_green` | on/off | 控制绿灯开关 |
| `set_blue` | on/off | 控制蓝灯开关 |
| `turn_off_all` | - | 关闭所有灯 |

### 颜色轮换命令

| 命令 | 参数 | 说明 |
|------|------|------|
| `start_cycle` | interval(可选) | 开始颜色轮换(默认1秒间隔) |
| `stop_cycle` | - | 停止颜色轮换 |

### 查询命令

| 命令 | 参数 | 说明 |
|------|------|------|
| `get_status` | - | 获取当前状态 |
| `help` | - | 显示帮助信息 |

## 响应格式

所有API响应均为JSON格式：

### 成功响应

```json
{
  "status": "success",
  "message": "红灯已开启",
  "data": { ... }  // 可选，包含详细数据
}
```

### 错误响应

```json
{
  "status": "error",
  "message": "错误描述"
}
```

## 示例

### Python代码示例

```python
from usb_lamp_controller import USBLampController

# 创建控制器实例
# macOS: controller = USBLampController(port='/dev/cu.usbserial-1330')
# Linux: controller = USBLampController(port='/dev/ttyUSB0')
# Windows: controller = USBLampController(port='COM3')
controller = USBLampController(port='/dev/cu.usbserial-1330')

# 独立控制灯光
controller.set_red(True)      # 开启红灯
controller.set_green(True)    # 开启绿灯
controller.turn_off_all()     # 关闭所有灯

# 颜色轮换
controller.start_color_cycle(interval=2.0)  # 每2秒轮换一次
# ... 等待一段时间 ...
controller.stop_color_cycle()  # 停止轮换

# 查询状态
status = controller.get_status()
print(status)
```

### Socket客户端示例

```python
import socket
import json

# 连接到服务器
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 8888))

# 发送命令
sock.send(b'set_red on\n')
response = json.loads(sock.recv(1024))
print(response)

sock.close()
```

## 自定义USB设备协议

如果需要控制特定的USB设备，需要修改 `usb_lamp_controller.py` 中的 `_send_usb_command` 方法：

```python
def _send_usb_command(self, color, state):
    # 根据实际设备协议实现USB通信
    # 示例1: HID设备
    # import usb.core
    # device = usb.core.find(idVendor=0xXXXX, idProduct=0xXXXX)
    # report = self._build_hid_report(color, state)
    # device.write(1, report)

    # 示例2: 串口设备
    # import serial
    # ser = serial.Serial('/dev/ttyUSB0', 9600)
    # command = self._build_serial_command(color, state)
    # ser.write(command)

    # 示例3: 厂商自定义协议
    # 根据厂商文档实现具体协议

    print(f"发送命令: {color.value} -> {state}")
```

## 常见问题

### Q: 程序运行正常但灯不亮？

A: 默认实现是模拟模式，需要根据实际USB设备修改 `_send_usb_command` 方法。

### Q: 如何修改颜色轮换顺序？

A: 修改 `usb_lamp_controller.py` 中的 `self.colors` 列表：

```python
self.colors = [
    LightColor.RED,
    LightColor.GREEN,
    LightColor.BLUE,
    # 添加更多颜色组合
    # LightColor.RED + LightColor.GREEN  # 需要修改代码支持
]
```

### Q: 如何同时显示多种颜色？

A: 程序已支持组合颜色，例如同时开启红、绿灯会产生黄色。

### Q: 服务器可以支持多少客户端？

A: Socket服务器支持多客户端同时连接，每个客户端独立处理。

## 许可证

本项目采用MIT许可证。

## 作者

Claude Code - Anthropic官方CLI工具
