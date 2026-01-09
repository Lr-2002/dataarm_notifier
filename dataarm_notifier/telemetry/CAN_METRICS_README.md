# CAN Metrics Integration

CAN Bus 实时监控与 Rerun 可视化集成系统。

## 架构概览

```
┌─────────────────┐         TCP          ┌─────────────────┐
│   can_monitor   │ ──────────────────►  │    notifier     │
│  (control 进程)  │    JSON/9877        │  (独立进程)       │
└────────┬────────┘                      └────────┬────────┘
         │                                        │
         │ sends metrics/events/mapping            │ logs to Rerun
         ▼                                        ▼
┌─────────────────────────────────────────────────────────┐
│                      Rerun Viewer                       │
│  can/bus/*  |  can/rtt/*  |  can/joint/*  |  notify/*  │
└─────────────────────────────────────────────────────────┘
```

## 组件

### 1. CAN Metrics Client (`control/hardware/can_monitor/client_adapter.py`)

TCP 客户端，运行在 `can_monitor` 进程中，发送 CAN 指标到 notifier。

**主要功能：**
- `send_metrics(metrics)` - 发送聚合指标
- `send_event(event)` - 发送 CAN 事件
- `send_mapping(mapping)` - 发送 CAN ID 到关节名称映射
- 5秒自动重连机制

**使用方法：**
```python
from hardware.can_monitor import CANMetricsClient

client = CANMetricsClient(host="127.0.0.1", port=9877)
await client.connect()
await client.send_metrics(metrics_data)
await client.stop()
```

### 2. CAN Metrics Server (`notifier/telemetry/can_metrics_server.py`)

TCP 服务器，运行在 `notifier` 进程中，接收数据并可视化。

**主要功能：**
- 监听 TCP 9877 端口
- 解析 JSON 消息 (metrics/event/mapping)
- Rerun 实时可视化

**使用方法：**
```python
from dataarm_notifier.telemetry import CANMetricsServer

server = CANMetricsServer(port=9877, app_name="CAN_Monitor")
await server.start()
```

### 3. Producer 集成 (`notifier/telemetry/producer.py`)

`TelemetryProducer` 提供了便捷方法：

```python
producer = TelemetryProducer(app_name="Robot_Telemetry")
producer.start_can_server(port=9877)
# ... 使用完毕后
producer.stop_can_server()
```

### 4. CLI 集成 (`control/hardware/can_monitor/cli.py`)

```bash
# 启动 can_monitor 并发送到 notifier
python3 -m hardware.can_monitor.cli \
    --interface can0 \
    --notifier-host 127.0.0.1 \
    --notifier-port 9877
```

## 消息协议

### Metrics 消息

```json
{
  "type": "metrics",
  "timestamp_ns": 1234567890000000000,
  "data": {
    "bus_load_percent": 25.5,
    "total_frames": 12345,
    "active_ids": 6,
    "error_frames_per_second": 0.0,
    "dropped_frames_per_second": 0.0,
    "per_id_stats": {
      "1": {"fps_window": 500.0, "dt_p95_ms": 1.5},
      "2": {"fps_window": 500.0, "dt_p95_ms": 1.2}
    },
    "per_pair_rtt": {
      "[1,17]": {"rtt_mean_ms": 2.1, "rtt_p95_ms": 3.5}
    }
  }
}
```

### Event 消息

```json
{
  "type": "event",
  "timestamp_ns": 1234567890000000000,
  "data": {
    "event_type": "timeout",
    "can_id": 17,
    "details": {"rtt_ms": 55.0, "send_id": "0x01"}
  }
}
```

**事件类型：**
- `timeout` - RTT 超时
- `error_frame` - CAN 错误帧
- `high_temp` - 高温告警
- `watchdog` - 看门狗触发
- `drop` - 帧丢失

### Mapping 消息

```json
{
  "type": "mapping",
  "timestamp_ns": 1234567890000000000,
  "data": {
    "can_id_map": {"1": 17, "2": 18},
    "joint_names": {
      "1": "shoulder_joint",
      "17": "shoulder_response"
    }
  }
}
```

## Rerun 数据路径

### 总线监控 (can/bus/)

| 路径 | 类型 | 描述 |
|------|------|------|
| `can/bus/load` | Scalar | 总线负载百分比 |
| `can/bus/frames_total` | Scalar | 总帧数 |
| `can/bus/active_ids` | Scalar | 活跃 CAN ID 数 |

### RTT 监控 (can/rtt/)

| 路径 | 类型 | 描述 |
|------|------|------|
| `can/rtt/mean` | Scalar | RTT 均值 (ms) |
| `can/rtt/p95` | Scalar | RTT P95 (ms) |
| `can/joint/{name}/rtt` | Scalar | 单关节 RTT |

### 关节统计 (can/joint/)

| 路径 | 类型 | 描述 |
|------|------|------|
| `can/joint/{name}/fps` | Scalar | 关节帧率 |
| `can/joint/{name}/jitter_p95` | Scalar | 抖动 P95 (ms) |

### 通知 (notify/)

| 路径 | 类型 | 描述 |
|------|------|------|
| `notify/dashboard` | TextDocument | 状态面板 |
| `notify/log` | TextLog | 事件日志 |

## 状态阈值

| 状态 | 总线负载 | 错误率 | 颜色 |
|------|---------|--------|------|
| NOMINAL | < 50% | < 0.1/s | 🟢 绿色 |
| WARNING | 50-80% | 0.1-1.0/s | 🟡 黄色 |
| ERROR | >= 80% | > 1.0/s | 🔴 红色 |

## 快速开始

### 1. 启动 Notifier

```bash
cd /home/lr-2002/project/DataArm/dataarm/notifier

# 单独启动 CAN metrics server
python3 -c "
from dataarm_notifier.telemetry import CANMetricsServer
import asyncio

async def main():
    server = CANMetricsServer(port=9877, app_name='CAN_Monitor')
    await server.start()

asyncio.run(main())
"

# 或使用完整 CLI
python3 -m dataarm_notifier.cli_telemetry
```

### 2. 启动 Can Monitor

```bash
cd /home/lr-2002/project/DataArm/dataarm/control

# 发送到 notifier
python3 -m hardware.can_monitor.cli \
    --interface can0 \
    --notifier-host 127.0.0.1 \
    --notifier-port 9877

# 或使用 dummy notifier (仅控制台输出)
python3 -m hardware.can_monitor.cli --interface can0
```

### 3. 查看 Rerun

连接 Rerun viewer:
```bash
rerun --connect rerun+http://127.0.0.1:9876/proxy
```

或在 Rerun viewer 中选择 TCP 连接 `127.0.0.1:9876`。

## 测试

### 单元测试

```bash
cd /home/lr-2002/project/DataArm/dataarm/notifier
python3 -m pytest tests/telemetry/ -v
```

### 模拟数据测试

```bash
python3 test_can_metrics_mock.py
```

测试内容：
- TCP 连接与数据传输
- 各类消息格式
- 状态转换 (NOMINAL -> WARNING -> ERROR)
- 事件处理
- 重连行为

## 配置

### 环境变量

```bash
# Notifier 端口 (可选，默认 9877)
export NOTIFIER_CAN_PORT=9877
```

### 端口分配

| 端口 | 服务 |
|------|------|
| 9876 | Rerun TCP |
| 9877 | CAN Metrics TCP |

## 故障排除

### 连接失败

1. 检查 notifier 是否正在运行
2. 确认防火墙允许 9877 端口
3. 验证 host 地址正确

```bash
# 测试端口连通性
nc -zv 127.0.0.1 9877
```

### 无数据显示

1. 检查 can_monitor 日志
2. 确认 `send_metrics` 被正确调用
3. 验证消息格式正确

### 重连风暴

客户端有 5 秒重连间隔，避免频繁重试。

## 依赖

### Notifier 端

- `rerun-sdk` - Rerun 可视化
- `python >= 3.10`

### Control 端

- `asyncio` - 异步 TCP
- `can_monitor` 模块 (现有依赖)

## 架构决策

| 决策 | 理由 |
|------|------|
| TCP Socket | 两进程解耦，进程重启不影响 |
| JSON 格式 | 易于调试和扩展 |
| 5秒重连 | 平衡可靠性和资源 |
| 独立端口 | 避免 Rerun 端口冲突 |
| 优先级映射 | can_monitor 提供 > config.json |
