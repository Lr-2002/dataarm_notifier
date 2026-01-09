# Data Model: CAN Metrics Integration

## Architecture: Two-Process TCP Communication

```
┌─────────────────────┐         TCP 9877          ┌─────────────────────┐
│   can_monitor       │ ───────────────────────→ │     Notifier        │
│   (control)         │   JSON messages          │     (notifier)      │
└─────────────────────┘                          └─────────────────────┘
```

## Key Entities

### CANMetricsServer (notifier)

**Purpose**: TCP server receiving CAN metrics from can_monitor

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `_port` | int | Server port (default: 9877) |
| `_producer` | TelemetryProducer | Rerun logging backend |
| `_can_id_to_name` | Dict[int, str] | CAN ID to joint name mapping |
| `_running` | bool | Server running state |

**Methods**:

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `start()` | None | None | Start async TCP server |
| `stop()` | None | None | Stop server |
| `_handle_client()` | reader, writer | None | Handle client connection |
| `_parse_message()` | dict | str | Parse message type |
| `_handle_metrics()` | dict | None | Log metrics to Rerun |
| `_handle_event()` | dict | None | Log event to Rerun |
| `_handle_mapping()` | dict | None | Update ID mapping |

### CANMetricsClient (can_monitor)

**Purpose**: TCP client sending CAN metrics to notifier

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `_host` | str | Server host |
| `_port` | int | Server port |
| `_writer` | StreamWriter | TCP writer |
| `_connected` | bool | Connection state |

**Methods**:

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `connect()` | None | bool | Connect to server |
| `send_metrics()` | AggregatedMetrics | None | Send metrics |
| `send_event()` | CANEvent | None | Send event |
| `close()` | None | None | Close connection |

## Message Protocol (JSON over TCP)

### Message Envelope

```json
{
  "type": "metrics" | "event" | "mapping" | "ping",
  "timestamp_ns": int,
  "data": { ... }
}
```

### metrics message

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

### event message

```json
{
  "type": "event",
  "timestamp_ns": 1234567890,
  "data": {
    "event_type": "timeout" | "error_frame" | "high_temp" | "watchdog" | "drop",
    "can_id": 17,
    "details": {"rtt_ms": 55.0}
  }
}
```

### mapping message

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

### ping message (request mapping)

```json
{
  "type": "ping",
  "timestamp_ns": 1234567890,
  "data": {}
}
```

Response:
```json
{
  "type": "mapping",
  "timestamp_ns": 1234567890,
  "data": { ... }
}
```

## AggregatedMetrics (external)

From dataarm can_monitor module - used as reference for JSON schema.

## CANEvent (external)

From dataarm can_monitor module - used as reference for JSON schema.

## Rerun Path Mapping

| Rerun Path | Source Field | Type |
|------------|--------------|------|
| `can/bus/load` | data.bus_load_percent | Scalar |
| `can/bus/frames_total` | data.total_frames | Scalar |
| `can/bus/active_ids` | data.active_ids | Scalar |
| `can/rtt/mean` | computed mean from per_pair_rtt | Scalar |
| `can/rtt/p95` | computed p95 from per_pair_rtt | Scalar |
| `can/joint/{name}/fps` | per_id_stats[can_id].fps_window | Scalar |
| `can/joint/{name}/jitter_p95` | per_id_stats[can_id].dt_p95_ms | Scalar |

## Event Severity Mapping

| CANEventType | StatusLevel | Rerun Path |
|--------------|-------------|------------|
| TIMEOUT | WARNING | notify/log |
| ERROR_FRAME | ERROR | notify/log |
| HIGH_TEMP | WARNING | notify/log |
| WATCHDOG | ERROR | notify/log |
| DROP | WARNING | notify/log |

## State Transitions

```
DISCONNECTED
  → CONNECTING (can_monitor starts)
  → CONNECTED (TCP handshake complete)
  → RECEIVING (metrics flowing)
  → DISCONNECTED (network error)
  → WAITING (5 second delay)
  → CONNECTING (reconnect attempt)
```

## ID Mapping Fallback Logic

```
1. can_monitor 发送 mapping 消息?
   YES → 使用 can_monitor 的 mapping
   NO  → 从 config.json 加载 mapping

2. 连接断开重连成功后:
   - 重新请求 mapping (发送 ping 消息)
   - 如果 can_monitor 不响应，继续使用旧的 mapping
```

```
IDLE (no data)
  → NOMINAL (bus_load < 50%, no errors)
  → WARNING (50% <= bus_load < 80% OR errors present)
  → ERROR (bus_load >= 80% OR timeout events)
```

## Validation Rules

1. Message MUST have "type" field
2. Message MUST have "timestamp_ns" field
3. Message MUST have "data" field
4. Unknown message types SHOULD be logged and ignored
5. JSON parse errors SHOULD close connection
