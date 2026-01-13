# Implementation Plan: CAN Monitor Integration

**Feature**: CAN Monitor Integration
**Branch**: `001-can-monitor-integration`
**Created**: 2026-01-09
**Status**: Planning

## Architecture

```
┌─────────────────────┐         TCP/IP          ┌─────────────────────┐
│   can_monitor       │    (localhost:9877)     │     Notifier        │
│   (control)         │ ──────────────────────→ │     (notifier)      │
│                     │                         │                     │
│  - SocketClient     │   AggregatedMetrics     │  - SocketServer     │
│  - send_metrics()   │   CANEvent              │  - CANMetricsServer │
│  - send_event()     │                         │  - Rerun logging    │
└─────────────────────┘                         └─────────────────────┘
```

**关键决策**:
- 进程隔离: can_monitor 和 notifier 是独立进程
- 通信协议: TCP Socket (JSON over TCP)
- 端口: 9877 (Rerun 用 9876，避免冲突)
- 数据序列化: JSON (兼容 Python dict)

## Technical Context

### Unknowns (RESOLVED)

1. **Joint Name Mapping**: 如何获取 CAN ID → 关节名称 映射？
   - **决策**: 优先使用 can_monitor 提供的 mapping，否则从 config.json 读取
   - can_monitor 发送 `mapping` 消息 → notifier 使用
   - 如果没收到 mapping → notifier 从 config 加载

2. **重连策略**: can_monitor 连接失败后？
   - **决策**: 每 5 秒重试一次，无限重试直到成功
   - 断线时打印 INFO 日志，不抛出异常

### Design Decisions (Resolved)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| IPC | TCP Socket | 跨平台、简单、可跨机器 |
| Port | 9877 | 避免与 Rerun 9876 冲突 |
| Protocol | JSON over TCP | 易于调试、兼容性好 |
| 序列化 | json + base64 (bytes) | 处理二进制数据 |
| Server | notifier 端 | notifier 启动服务，can_monitor 连接 |

## Phase 1: Design

### 通信协议

**Client → Server 消息格式**:

```json
{
  "type": "metrics",
  "timestamp_ns": 1234567890,
  "data": {
    "bus_load_percent": 25.5,
    "error_frames_per_second": 0.0,
    "dropped_frames_per_second": 0.0,
    "total_frames": 12345,
    "active_ids": 6,
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

```json
{
  "type": "event",
  "timestamp_ns": 1234567890,
  "data": {
    "event_type": "timeout",
    "can_id": 17,
    "details": {"rtt_ms": 55.0, "send_id": "0x01"}
  }
}
```

```json
{
  "type": "mapping",
  "timestamp_ns": 1234567890,
  "data": {
    "can_id_map": {"1": 17, "2": 18, "3": 19},
    "joint_names": {"1": "shoulder_joint", "17": "shoulder_response"}
  }
}
```

### Data Model

```python
# telemetry/can_metrics_server.py

class CANMetricsServer:
    """TCP Server receiving CAN metrics from can_monitor."""

    def __init__(self, port: int = 9877, producer: TelemetryProducer):
        self._port = port
        self._producer = producer
        self._can_id_to_name: Dict[int, str] = {}
        self._running = False

    async def start(self) -> None:
        """Start TCP server."""
        pass

    async def _handle_client(self, reader: asyncio.StreamReader, ...) -> None:
        """Handle client connection."""
        pass

    def _parse_message(self, data: dict) -> None:
        """Parse and route message to handler."""
        pass

    def _handle_metrics(self, data: dict) -> None:
        """Log metrics to Rerun."""
        pass

    def _handle_event(self, data: dict) -> None:
        """Log event to Rerun."""
        pass

    def _handle_mapping(self, data: dict) -> None:
        """Update CAN ID mapping."""
        pass
```

```python
# can_monitor/client_adapter.py

class CANMetricsClient:
    """TCP Client sending metrics to notifier with auto-reconnect."""

    RECONNECT_INTERVAL = 5.0  # seconds

    def __init__(self, host: str = "127.0.0.1", port: int = 9877):
        self._host = host
        self._port = port
        self._reader = None
        self._writer = None
        self._running = False

    async def connect(self) -> bool:
        """Connect to notifier server."""
        pass

    async def _reconnect_loop(self) -> None:
        """Background loop: try connect every 5 seconds."""
        while self._running:
            try:
                if await self.connect():
                    # Connected! Start sending metrics
                    await self._send_loop()
                else:
                    # Connection refused, wait and retry
                    await asyncio.sleep(self.RECONNECT_INTERVAL)
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(self.RECONNECT_INTERVAL)

    async def send_metrics(self, metrics: AggregatedMetrics) -> None:
        """Send metrics to server."""
        pass

    async def send_event(self, event: CANEvent) -> None:
        """Send event to server."""
        pass

    async def close(self) -> None:
        """Close connection."""
        pass
```

### Rerun Paths (保持不变)

| Path | Type | Description |
|------|------|-------------|
| `can/bus/load` | Scalar | Bus load percentage |
| `can/bus/frames_total` | Scalar | Total frames |
| `can/bus/active_ids` | Scalar | Active IDs |
| `can/rtt/mean` | Scalar | Mean RTT |
| `can/rtt/p95` | Scalar | P95 RTT |
| `can/joint/{name}/fps` | Scalar | Per-joint FPS |
| `can/joint/{name}/jitter_p95` | Scalar | Per-joint jitter |
| `notify/log` | TextLog | Events |

## Phase 2: Implementation Steps

### Step 1: Create CAN Metrics Server (notifier 端)

**File**: `telemetry/can_metrics_server.py`

- `CANMetricsServer` 类 (async TCP server)
- `_handle_metrics()` → Rerun logging
- `_handle_event()` → Rerun event log
- `_handle_mapping()` → 更新 ID 映射

### Step 2: Update TelemetryProducer

**File**: `telemetry/producer.py`

- 添加 `start_can_server(port=9877)` 方法
- 添加 `stop_can_server()` 方法

### Step 3: Create CAN Metrics Client (control 端)

**文件位置**: control/hardware/can_monitor/client_adapter.py

- `CANMetricsClient` 类 (async TCP client)
- 实现 `send_metrics()`, `send_event()`
- 自动重连逻辑

### Step 4: 修改 can_monitor CLI

**文件**: control/hardware/can_monitor/cli.py

- 添加 `--notifier-host/port` 参数
- 使用 `CANMetricsClient` 替代 `DummyNotifierAPI`

### Step 5: 单元测试

**文件**: `tests/telemetry/test_can_metrics_server.py`

- 测试消息解析
- 测试 Rerun logging
- 测试连接/断开

## 文件结构

```
notifier/
├── dataarm_notifier/telemetry/
│   ├── __init__.py                    # 导出 CANMetricsServer
│   ├── producer.py                    # 添加 server 方法
│   └── can_metrics_server.py          # NEW: TCP server

control/hardware/can_monitor/
├── __init__.py                        # 导出 CANMetricsClient
├── client_adapter.py                  # NEW: TCP client
└── cli.py                             # 添加 --notifier-* 参数
```

## 配置

### Notifier 启动
```bash
python -m dataarm_notifier.telemetry \
    --rerun-app-name "Robot" \
    --can-server-port 9877 \
    --no-simulation
```

### can_monitor 启动
```bash
python -m control.hardware.can_monitor.cli \
    --interface can0 \
    --notifier-host 127.0.0.1 \
    --notifier-port 9877
```

## Dependencies

| 端 | 依赖 |
|----|------|
| notifier | asyncio, json |
| can_monitor | asyncio, json |

## Success Metrics

- SC-001: 数据在 100ms 内从 can_monitor 到达 notifier
- SC-002: 网络断开后 can_monitor 自动重连
- SC-003: 所有事件在 500ms 内显示在 Rerun
