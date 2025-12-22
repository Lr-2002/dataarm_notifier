#!/usr/bin/env python3
"""Test Robot State Notifier with all colors and recording flow."""

import time
from dataarm_notifier import RobotStateNotifier, RobotState, RecordingController


def test_colors():
    """Test all state colors."""
    print("=" * 50)
    print("Testing all state colors")
    print("=" * 50)

    notifier = RobotStateNotifier(port='/dev/ttyUSB1')

    states = [
        (RobotState.IDLE, "CYAN (G+B)"),
        (RobotState.TEACH, "GREEN"),
        (RobotState.SAVING, "YELLOW (R+G)"),
        (RobotState.EXECUTE_STOPPED, "BLUE"),
        (RobotState.EXECUTE_RUNNING, "WHITE"),
        (RobotState.ERROR, "RED"),
    ]

    for state, color in states:
        print(f"\n{state.value}: {color}")
        notifier.set_state(state)
        time.sleep(1.5)

    notifier.cleanup()
    print("\nColor test complete!")


def test_recording_controller():
    """Test recording controller with keyboard."""
    print("\n" + "=" * 50)
    print("Testing Recording Controller")
    print("=" * 50)
    print("Press ENTER to start/stop recording")
    print("Press Ctrl+C to exit")
    print("=" * 50)

    def on_start():
        print(">>> Recording started!")

    def on_stop():
        print(">>> Recording stopped!")

    controller = RecordingController(port='/dev/ttyUSB1', saving_duration=3.0)
    controller.on_recording_start(on_start)
    controller.on_recording_stop(on_stop)

    try:
        controller.start()
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        controller.stop()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "record":
        test_recording_controller()
    else:
        test_colors()
        print("\nRun with 'record' argument to test keyboard recording:")
        print("  python3 test_state_notifier.py record")
