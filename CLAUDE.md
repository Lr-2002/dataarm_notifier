# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

DataArm Notifier is a USB lamp controller for robot state indication, now extended with Real-Time Telemetry & Notification capabilities using Rerun SDK.

## New Feature: Telemetry Module

**Feature Branch**: `001-rerun-telemetry`

### Architecture

The telemetry system uses a Client-Server architecture via Rerun SDK:
- **Producer**: Sends telemetry data over TCP localhost
- **Consumer**: Rerun Viewer receives and visualizes data
- **Decoupled**: Viewer restart doesn't affect robot control

### Source Structure

```
dataarm_notifier/
├── telemetry/
│   ├── __init__.py
│   ├── producer.py      # TelemetryProducer class
│   ├── consumer.py      # TelemetryConsumer class
│   ├── simulation.py    # Built-in simulation profiles
│   └── config.py        # YAML configuration
├── tests/
│   └── telemetry/
│       ├── test_producer.py
│       ├── test_consumer.py
│       └── test_simulation.py
└── cli/
    └── telemetry_cli.py
```

### Key Components

1. **TelemetryProducer**: Logs position, velocity, dynamics, camera feeds
2. **SimulationEngine**: Built-in simulation with configurable profiles
3. **Rerun Paths**: Hierarchical naming for auto-grouping plots

### Data Paths

| Path | Data Type | Purpose |
|------|-----------|---------|
| `drive/pos/target` | Scalar | Target position |
| `drive/pos/actual` | Scalar | Actual position |
| `drive/vel/raw` | Scalar | Raw velocity |
| `drive/vel/filtered` | Scalar | Filtered velocity |
| `drive/torque` | Scalar | Motor torque |
| `sensors/camera_main` | Image | Camera feed |
| `notify/dashboard` | TextDocument | Status dashboard |
| `notify/log` | TextLog | Event log |

### Dependencies

- `rerun-sdk` - Visualization
- `opencv-python` - Camera capture
- `pyyaml` - Configuration
- `numpy` - Data manipulation

### Configuration

YAML config files support:
- Simulation profiles (sine, step, ramp, torque_threshold)
- Threshold settings for alerts
- Frequency and buffer settings

### Testing Strategy

- Use built-in simulation mode for testing without hardware
- Mock Rerun SDK and camera for unit tests
- 80% coverage requirement

## Original Notifier Features

The original USB lamp controller features remain available:
- 7-color state indication (RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, WHITE)
- Robot state visualization (IDLE, TEACH, EXECUTE, SAVING, ERROR)
- Keyboard-triggered recording control
- Auto port detection for USB serial devices

### State Colors

| State | Color | RGB |
|-------|-------|-----|
| IDLE | CYAN | G+B |
| TEACH (recording) | GREEN | G |
| SAVING | YELLOW | R+G |
| EXECUTE (stopped) | BLUE | B |
| EXECUTE (running) | WHITE | R+G+B |
| ERROR | RED | R |

### USB Protocol

- Baud Rate: 4800
- Data Bits: 8
- Parity: None
- Stop Bits: 2
- Protocol: Modbus RTU
