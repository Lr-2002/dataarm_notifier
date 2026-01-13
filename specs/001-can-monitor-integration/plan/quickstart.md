# Quickstart: CAN Monitor Integration

## Overview

This guide helps you set up the two-process CAN Monitor Integration:
- **can_monitor** (control process): Captures CAN frames and sends metrics via TCP
- **Notifier** (notifier process): Receives metrics via TCP and visualizes in Rerun

## Architecture

```
┌─────────────────────┐         TCP 9877          ┌─────────────────────┐
│   can_monitor       │ ───────────────────────→ │     Notifier        │
│   (control)         │   JSON messages          │     (notifier)      │
└─────────────────────┘                          └─────────────────────┘
```

## Prerequisites

- Python 3.8+
- rerun-sdk installed
- DataArm control and notifier installed

## Installation

```bash
# Install notifier
pip install -e /path/to/dataarm/notifier

# Ensure can_monitor is available
export PYTHONPATH="/path/to/dataarm/control:$PYTHONPATH"
```

## Usage

### 1. Start Notifier (Rerun Server)

```bash
# Start notifier with CAN metrics server on port 9877
python -m dataarm_notifier.telemetry \
    --rerun-app-name "Robot" \
    --can-server-port 9877 \
    --no-simulation
```

This starts:
- Rerun viewer on TCP 9876
- CAN metrics server on TCP 9877

### 2. Start can_monitor

```bash
# Start can_monitor with notifier connection
python -m control.hardware.can_monitor.cli \
    --interface can0 \
    --frequency 20 \
    --notifier-host 127.0.0.1 \
    --notifier-port 9877
```

## Rerun Viewer Layout

```
├─ drive/
│  ├─ pos/target
│  ├─ pos/actual
│  ├─ vel/raw
│  ├─ vel/filtered
│  ├─ torque
│  └─ acc_filtered
│
├─ can/                      # NEW: CAN metrics
│  ├─ bus/
│  │  ├─ load               - Bus load %
│  │  ├─ frames_total       - Total frames
│  │  └─ active_ids         - Active CAN IDs
│  ├─ rtt/
│  │  ├─ mean               - Mean RTT
│  │  └─ p95                - 95th percentile RTT
│  └─ joint/
│     ├─ shoulder_joint/
│     │  ├─ fps
│     │  └─ jitter_p95
│     └─ upper_arm_joint/
│        ├─ fps
│        └─ jitter_p95
│
├─ sensors/
│  └─ camera_main
│
└─ notify/
   ├─ dashboard
   └─ log                  - Event log
```

## Programmatic Usage

### Notifier (Python)

```python
from dataarm_notifier.telemetry import TelemetryProducer

import asyncio


async def main():
    producer = TelemetryProducer(app_name="Robot")
    producer.start_can_server(port=9877)
    await asyncio.sleep(float("inf"))


asyncio.run(main())
```

### can_monitor Integration

```python
from control.hardware.can_monitor import CANMonitor, CANMetricsClientNotifier

def main():
    notifier = CANMetricsClientNotifier(host="127.0.0.1", port=9877, publish_interval_ms=50.0)
    monitor = CANMonitor(notifier=notifier, can_interface="can0")
    monitor.start()

main()
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATAARM_CAN_INTERFACE` | CAN interface | can0 |
| `DATAARM_RERUN_PORT` | Rerun port | 9876 |
| `DATAARM_CAN_SERVER_PORT` | CAN metrics server port | 9877 |
| `DATAARM_NOTIFIER_HOST` | Notifier host | 127.0.0.1 |

### Command Line Options

**Notifier:**
```bash
--rerun-app-name NAME      # Rerun app name
--can-server-port PORT     # CAN metrics server port (default: 9877)
```

**can_monitor:**
```bash
--interface, -i            # CAN interface (default: can0)
--frequency, -f            # Publish frequency Hz (default: 20)
--notifier-host            # Notifier host (default: 127.0.0.1)
--notifier-port            # Notifier port (default: 9877)
--fd / --no-fd             # Enable/disable CAN-FD
```

## Troubleshooting

### Not Connected

1. Check notifier is running: `netstat -tlnp | grep 9877`
2. Check can_monitor logs for connection errors
3. Verify firewall allows localhost connections
4. can_monitor will retry every 5 seconds automatically

### Automatic Reconnection

- If can_monitor loses connection to notifier:
  - Logs: "Connection lost, retrying in 5s..."
  - Retries every 5 seconds until successful
- No manual intervention required

### No Data Appearing

1. Check can_monitor is receiving CAN frames
2. Verify Rerun viewer is connected
3. Check joint name mapping is set

### High Latency

1. Reduce publish frequency: `--frequency 10`
2. Check network latency: `ping 127.0.0.1`
3. Verify CPU not overloaded

## Next Steps

- See [data-model.md](./data-model.md) for protocol details
- See [plan.md](./plan.md) for implementation details
