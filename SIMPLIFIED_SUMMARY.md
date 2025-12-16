# 简化总结 - 三色灯控制器

## 更新说明

根据用户要求，已重新整理README并修缮相关代码，专注于**三种颜色（红、绿、蓝）**的控制功能。

## 主要变更

### 1. README.md 重新整理

**更新内容**：
- ✅ 强调支持三种颜色的灯（红、绿、蓝）
- ✅ 移除白灯相关说明
- ✅ 简化项目结构，移除多余测试脚本
- ✅ 更新使用示例，按照 `test_three_light.py` 的逻辑编写
- ✅ 简化API命令说明，只保留三种颜色和关闭功能
- ✅ 更新颜色轮换间隔为2秒

**主要章节**：
- 功能特性：只说明三种颜色控制
- 使用方法：将 `test_three_light.py` 作为推荐使用方式
- API命令：只保留 `set_red`、`set_green`、`set_blue`、`turn_off_all`
- 示例代码：按照红→蓝→绿的顺序编写

### 2. socket_client.py 简化

**更新内容**：
- ✅ 简化交互模式，只显示四种命令
  - `set_red on|off`
  - `set_green on|off`
  - `set_blue on|off`
  - `turn_off_all`
- ✅ 移除其他复杂命令（start_cycle、stop_cycle、get_status、help）
- ✅ 保留批量模式功能

### 3. socket_server.py 更新

**更新内容**：
- ✅ 更新help命令说明，间隔时间改为2秒
- ✅ 更新start_cycle默认间隔为2秒
- ✅ 保留所有命令处理（服务器端完整功能）

## test_three_light.py 逻辑

按照用户创建的测试脚本，标准使用流程为：

```python
from usb_lamp_controller import USBLampController
import time

lamp = USBLampController()

lamp.set_red()      # 开启红灯
time.sleep(1)       # 停顿1秒

lamp.set_blue()     # 开启蓝灯
time.sleep(1)       # 停顿1秒

lamp.set_green()    # 开启绿灯
time.sleep(1)       # 停顿1秒

lamp.turn_off_all() # 关闭所有灯
```

## 颜色轮换

**默认轮换顺序**：红 → 绿 → 蓝 → 红...

**间隔时间**：2秒

**轮换逻辑**（严格三步）：
1. 关掉灯 - 关闭所有灯
2. 打开灯开关 - 发送灯光开命令
3. 调整到目标灯的数值亮度 - 设置目标颜色亮度

## Socket API

### 支持的命令

| 命令 | 参数 | 说明 |
|------|------|------|
| `set_red` | on/off | 控制红灯开关 |
| `set_green` | on/off | 控制绿灯开关 |
| `set_blue` | on/off | 控制蓝灯开关 |
| `turn_off_all` | - | 关闭所有灯 |
| `start_cycle` | interval(可选) | 开始颜色轮换(默认2秒间隔) |
| `stop_cycle` | - | 停止颜色轮换 |
| `get_status` | - | 获取当前状态 |

### 使用示例

**单命令模式**：
```bash
python socket_client.py --command "set_red on"
python socket_client.py --command "set_green on"
python socket_client.py --command "set_blue on"
python socket_client.py --command "turn_off_all"
```

**交互模式**：
```bash
python socket_client.py
# 然后输入命令：set_red on, set_green on, set_blue on, turn_off_all, quit
```

## 项目文件

```
simple_notifier/
├── usb_lamp_controller.py    # 核心控制器
├── socket_server.py          # Socket API服务器
├── socket_client.py          # Socket客户端（已简化）
├── demo.py                   # 演示程序
├── test_three_light.py       # 三色灯测试脚本（推荐）
├── requirements.txt          # 依赖包
└── README.md                 # 说明文档（已重新整理）
```

## 设备信息

- **设备路径**: `/dev/cu.usbserial-1330` (macOS)
- **波特率**: 4800
- **数据格式**: 8位，无校验，2位停止位
- **协议**: Modbus RTU (0x06写寄存器)
- **CRC16**: 标准CRC16-MODBUS

## 寄存器地址

| 地址 | 功能 | 说明 |
|------|------|------|
| 0x0002 | 蓝灯 | 控制蓝灯亮度 |
| 0x0003 | 绿灯 | 控制绿灯亮度 |
| 0x0004 | 灯光开关 | 控制灯光总开关 |
| 0x0008 | 红灯 | 控制红灯亮度 |

## 亮度控制

**亮度计算**: PWM值 = 1999 × (亮度百分比 / 100)

**示例**:
- 100%亮度: 1999 (0x07CF)
- 50%亮度: 999 (0x03E7)
- 25%亮度: 499 (0x01F3)
- 10%亮度: 199 (0x00C7)

## 快速开始

```bash
# 1. 安装依赖
pip install pyserial

# 2. 运行三色灯测试（推荐）
python test_three_light.py

# 3. 运行演示程序
python demo.py

# 4. 启动Socket服务器
python socket_server.py

# 5. 测试Socket客户端
python socket_client.py --command "set_red on"
```

## 总结

**项目状态**: ✅ 已简化完成
**支持颜色**: ✅ 三种（红、绿、蓝）
**颜色轮换**: ✅ 间隔2秒
**Socket API**: ✅ 简化版客户端
**文档**: ✅ 重新整理，突出三色灯控制
**测试**: ✅ test_three_light.py 作为标准示例

系统已按照要求简化，专注于三色灯控制功能！🎉
