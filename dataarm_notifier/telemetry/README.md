# Robot Telemetry Visualization Module

Real-time robot telemetry visualization using [Rerun SDK](https://www.rerun.io/).

## Quick Start

### Installation

```bash
pip install dataarm-notifier
```

### Minimal Example

```python
from dataarm_notifier import TelemetryProducer

producer = TelemetryProducer(app_name="MyRobot")

# Log some data
producer.log_position(target=1.0, actual=0.95)
producer.log_velocity(raw=0.5, filtered=0.48)
producer.log_dynamics(torque=0.3, acceleration=0.1)

producer.shutdown()
```

---

## Core Concepts

### TelemetryProducer

The main class for sending data to the Rerun viewer.

```python
from dataarm_notifier import TelemetryProducer

producer = TelemetryProducer(
    app_name="RobotApp",      # Name shown in Rerun viewer
    config_path=None,         # Optional YAML config path
    connect=None,             # Optional: connect to existing viewer
)
```

**Methods:**
- `log_position(target, actual)` - Log target vs actual position
- `log_velocity(raw, filtered)` - Log velocity data
- `log_dynamics(torque, acceleration)` - Log dynamics data
- `log_camera(frame)` - Log camera frame (RGB image)
- `log_event(level, message)` - Log status events
- `update_status(level, message)` - Update system status
- `log_simulation_data(data)` - Log simulated trajectory data
- `shutdown()` - Clean up resources

---

## How To: Common Tasks

### 1. Add a Data Point (Position Tracking)

```python
from dataarm_notifier import TelemetryProducer

producer = TelemetryProducer(app_name="PositionDemo")

# Log single position point
target_pos = 0.5    # Commanded position (radians)
actual_pos = 0.48   # Measured position (radians)

producer.log_position(target=target_pos, actual=actual_pos)

producer.shutdown()
```

**Visualization:** Shows two scalars comparing target vs actual position over time.

### 2. Continuous Data Stream

```python
import time
from dataarm_notifier import TelemetryProducer

producer = TelemetryProducer(app_name="StreamDemo")

# Simulate continuous data stream
for i in range(100):
    t = i * 0.01
    target = 0.5 * sin(t)      # Simulated target
    actual = target + 0.02 * cos(t * 10)  # With noise

    producer.log_position(target, actual)
    time.sleep(0.01)  # 100Hz

producer.shutdown()
```

### 3. Add Camera Frames

```python
import cv2
from dataarm_notifier import TelemetryProducer

producer = TelemetryProducer(app_name="CameraDemo")

# Open camera (device index 3 for USB Camera)
cap = cv2.VideoCapture(3)

while True:
    ret, frame = cap.read()
    if ret:
        # Convert BGR (OpenCV) to RGB (Rerun)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        producer.log_camera(frame_rgb)
    # ...

cap.release()
producer.shutdown()
```

**For simulated camera feed:**
```python
import numpy as np
from dataarm_notifier import TelemetryProducer

producer = TelemetryProducer(app_name="SimCameraDemo")

def create_test_frame():
    # Create simple test pattern
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[100:200, 200:400] = [0, 255, 0]  # Green rectangle
    return frame

producer.log_camera(create_test_frame())
producer.shutdown()
```

### 4. Log Velocity Data

```python
from dataarm_notifier import TelemetryProducer

producer = TelemetryProducer(app_name="VelocityDemo")

# Log raw and filtered velocity
producer.log_velocity(raw=0.523, filtered=0.500)  # rad/s

producer.shutdown()
```

### 5. Log Dynamics (Torque & Acceleration)

```python
from dataarm_notifier import TelemetryProducer

producer = TelemetryProducer(app_name="DynamicsDemo")

# Log torque (Nm) and acceleration (rad/s^2)
producer.log_dynamics(torque=0.25, acceleration=0.1)

producer.shutdown()
```

### 6. Add Events/Status Messages

```python
from dataarm_notifier import TelemetryProducer, StatusLevel

producer = TelemetryProducer(app_name="EventDemo")

# Log different severity events
producer.log_event(StatusLevel.INFO, "System initialized")
producer.log_event(StatusLevel.WARNING, "High velocity detected")
producer.log_event(StatusLevel.ERROR, "Motor temperature exceeded limit")

# Or update dashboard status
producer.update_status(StatusLevel.INFO, "System Nominal")

producer.shutdown()
```

### 7. Use Simulation Engine

```python
from dataarm_notifier import TelemetryProducer, SimulationEngine

producer = TelemetryProducer(app_name="SimulationDemo")
engine = SimulationEngine()

# Set simulation profile
engine.set_profile("sine_tracking")

# Run simulation
for i in range(100):
    data = engine.step(dt=0.01)
    producer.log_simulation_data(data)

producer.shutdown()
engine.shutdown()
```

---

## Configuration

Create a `telemetry_config.yaml` file:

```yaml
frequency: 100          # Data recording frequency (Hz)
buffer_size: 1000       # Maximum data points to buffer

thresholds:
  tracking_deviation: 0.3   # Position tracking error threshold
  torque_warning: 1.8       # Torque warning threshold (Nm)
  torque_error: 2.5         # Torque error threshold (Nm)
  velocity_max: 10.0        # Maximum velocity (rad/s)

profiles:
  sine_tracking:
    type: sine
    amplitude: 1.0
    frequency: 0.5
    phase: 0.0
    noise: 0.01
    lag: 0.02

  step_response:
    type: step
    amplitude: 0.5
    noise: 0.0
```

Load with custom config:
```python
producer = TelemetryProducer(
    app_name="CustomConfig",
    config_path="/path/to/config.yaml"
)
```

---

## Command Line Usage

### Run Examples

```bash
# Motion tracking demo
python -m dataarm_notifier.examples.telemetry_motion_tracking

# Dynamics visualization
python -m dataarm_notifier.examples.telemetry_dynamics

# Status alerts demo
python -m dataarm_notifier.examples.telemetry_alerts

# Simulation demo
python -m dataarm_notifier.examples.telemetry_simulation

# Camera streaming
python -m dataarm_notifier.examples.telemetry_camera --device 3
```

### CLI Commands

```bash
# Start telemetry stream
python -m dataarm_notifier.cli.telemetry_cli --app MyRobot --freq 100

# Connect to existing viewer
python -m dataarm_notifier.cli.telemetry_cli --connect 127.0.0.1:9876
```

---

## Viewing Data

### Local Viewer

The Rerun viewer opens automatically when you run a script. Data is streamed to `localhost:9876`.

### Connect to Remote Viewer

```python
# On the machine collecting data
producer = TelemetryProducer(app_name="Robot", connect="127.0.0.1:9876")

# On the viewing machine
rerun --connect 192.168.1.100:9876
```

### Using Socket API

```python
from dataarm_notifier import TelemetryProducer

# Create producer that connects to socket server
producer = TelemetryProducer(
    app_name="SocketDemo",
    connect="127.0.0.1:9876"  # Connect to existing viewer
)
```

---

## API Reference

### TelemetryProducer

```python
class TelemetryProducer:
    def __init__(self, app_name, config_path=None, connect=None)
    def log_position(self, target, actual, timestamp=None)
    def log_velocity(self, raw, filtered)
    def log_dynamics(self, torque, acceleration)
    def log_camera(self, frame)
    def log_event(self, level, message)
    def update_status(self, level, message)
    def log_simulation_data(self, data)
    def shutdown(self)
```

### StatusLevel

```python
from dataarm_notifier import StatusLevel

StatusLevel.DEBUG    # Debug information
StatusLevel.INFO     # Normal operation
StatusLevel.WARNING  # Warning conditions
StatusLevel.ERROR    # Error conditions
StatusLevel.CRITICAL # Critical conditions
```

### ProfileType

```python
from dataarm_notifier import ProfileType

ProfileType.SINE      # Sine wave trajectory
ProfileType.STEP      # Step response
ProfileType.RAMP      # Linear ramp
ProfileType.SQUARE    # Square wave
ProfileType.CUSTOM    # Custom trajectory
```

### SimulationEngine

```python
class SimulationEngine:
    def __init__(self, config_path=None)
    def set_profile(self, profile_name)
    def step(self, dt)
    def shutdown(self)
```

---

## Complete Example

```python
#!/usr/bin/env python3
"""Complete telemetry example with all features."""

import time
import numpy as np
from dataarm_notifier import (
    TelemetryProducer,
    SimulationEngine,
    StatusLevel,
)

def main():
    # Initialize producer and simulation
    producer = TelemetryProducer(app_name="CompleteDemo")
    engine = SimulationEngine()
    engine.set_profile("sine_tracking")

    print("Starting telemetry stream...")
    print("Connect Rerun viewer to localhost:9876")

    try:
        for i in range(500):
            # Generate simulated data
            data = engine.step(dt=0.01)

            # Log all telemetry data
            producer.log_position(data.target, data.actual)
            producer.log_velocity(data.velocity, data.velocity_filtered)
            producer.log_dynamics(data.torque, data.acceleration)

            # Log event occasionally
            if i == 0:
                producer.log_event(StatusLevel.INFO, "Demo started")

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        producer.shutdown()
        engine.shutdown()
        print("Done")

if __name__ == "__main__":
    main()
```

---

## Troubleshooting

### Camera Not Opening

```python
# Try different device indices
import cv2
for i in range(8):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"Camera found at index {i}: {frame.shape}")
            break
```

### Rerun Viewer Not Showing Data

1. Check if viewer is running: `ps aux | grep rerun`
2. Connect manually: `rerun --connect localhost:9876`
3. Check port: `netstat -tlnp | grep 9876`

### Low FPS

- Reduce frame resolution
- Decrease logging frequency
- Use simulated feed for testing

---

## File Structure

```
dataarm_notifier/telemetry/
├── __init__.py           # Module exports
├── producer.py           # TelemetryProducer class
├── enums.py              # StatusLevel, ProfileType
├── data_types.py         # Dataclasses
├── config.py             # Configuration management
├── simulation.py         # SimulationEngine
├── camera.py             # Camera utilities
└── README.md             # This file
```
