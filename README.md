# DataArm Notifier

A plug-and-play USB lamp controller for robot state indication. Supports RGB color combinations and keyboard-triggered recording control.

## Features

- **7 Colors**: RED, GREEN, BLUE, YELLOW (R+G), CYAN (G+B), MAGENTA (R+B), WHITE (R+G+B)
- **Robot State Indication**: Visual feedback for IDLE, TEACH, EXECUTE, SAVING, ERROR states
- **Keyboard Control**: Press Enter to toggle recording (no root required on X11)
- **Auto Port Detection**: Automatically finds USB serial device
- **Plug and Play**: Minimal configuration needed

## Quick Start

### Installation

```bash
pip install pyserial pynput
```

### Basic Usage

```python
from dataarm_notifier import RobotStateNotifier

# Auto-detect USB port
notifier = RobotStateNotifier()

# Set states
notifier.idle()       # CYAN
notifier.teach()      # GREEN (recording)
notifier.saving(3)    # YELLOW for 3 seconds
notifier.error()      # RED

notifier.cleanup()
```

### Recording Controller

```python
from dataarm_notifier import RecordingController

def on_start():
    print("Recording started!")

def on_stop():
    print("Recording stopped!")

controller = RecordingController(saving_duration=3.0)
controller.on_recording_start(on_start)
controller.on_recording_stop(on_stop)

# Press ENTER to toggle recording
controller.start()
```

## State Colors

| State | Color | RGB |
|-------|-------|-----|
| IDLE | CYAN | G+B |
| TEACH (recording) | GREEN | G |
| SAVING | YELLOW | R+G |
| EXECUTE (stopped) | BLUE | B |
| EXECUTE (running) | WHITE | R+G+B |
| ERROR | RED | R |

## API Reference

### RobotStateNotifier

```python
from dataarm_notifier import RobotStateNotifier, RobotState

notifier = RobotStateNotifier(port=None, auto_detect=True)

# State methods
notifier.set_state(RobotState.TEACH)
notifier.idle()
notifier.teach()
notifier.recording()  # alias for teach()
notifier.saving(duration=3.0, callback=None)
notifier.execute_start()
notifier.execute_stop()
notifier.error()

# Keyboard
notifier.on_enter_pressed(callback)
notifier.start_keyboard_listener()
notifier.stop_keyboard_listener()

# Cleanup
notifier.cleanup()
```

### RecordingController

```python
from dataarm_notifier import RecordingController

controller = RecordingController(port=None, saving_duration=3.0)

controller.on_recording_start(callback)
controller.on_recording_stop(callback)
controller.start()
controller.stop()

# Properties
controller.is_recording  # bool
controller.notifier      # RobotStateNotifier
```

### USBLampController (Low-level)

```python
from dataarm_notifier import USBLampController

lamp = USBLampController(port='/dev/ttyUSB1')

# Single colors
lamp.set_red()
lamp.set_green()
lamp.set_blue()
lamp.set_white()

# Combined colors
lamp.set_yellow()   # R+G
lamp.set_cyan()     # G+B
lamp.set_magenta()  # R+B

lamp.turn_off_all()
lamp.close()
```

## Hardware Protocol

- **Baud Rate**: 4800
- **Data Bits**: 8
- **Parity**: None
- **Stop Bits**: 2
- **Protocol**: Modbus RTU

### Register Map

| Address | Function |
|---------|----------|
| 0x0001 | White LED |
| 0x0002 | Blue LED |
| 0x0003 | Green LED |
| 0x0004 | Light switch |
| 0x0008 | Red LED |

## Project Structure

```
dataarm_notifier/
├── dataarm_notifier/
│   ├── __init__.py
│   ├── usb_lamp_controller.py    # Low-level lamp control
│   ├── keyboard_listener.py      # Keyboard detection (pynput)
│   ├── robot_state_notifier.py   # High-level state API
│   ├── color_cycle_controller.py # Color cycling
│   ├── socket_server.py          # Network API
│   └── socket_client.py          # Network client
├── test_state_notifier.py        # State test script
├── test_keyboard.py              # Keyboard test script
└── README.md
```

## Testing

```bash
# Test all colors
python test_state_notifier.py

# Test keyboard recording
python test_state_notifier.py record
```

## License

MIT
