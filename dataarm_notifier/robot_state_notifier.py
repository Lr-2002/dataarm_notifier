"""
Robot State Notifier - Plug and play module for robot state indication.

Provides visual feedback for robot states using USB lamp and keyboard control.

States and Colors:
    - IDLE:              CYAN (G+B)
    - TEACH/RECORDING:   GREEN
    - SAVING:            YELLOW (R+G)
    - EXECUTE_STOPPED:   BLUE
    - EXECUTE_RUNNING:   WHITE
    - ERROR:             RED
"""

import glob
import time
import threading
from enum import Enum
from typing import Callable, Optional

from .usb_lamp_controller import USBLampController
from .keyboard_listener import KeyboardListener


class RobotState(Enum):
    """Robot state enumeration."""
    IDLE = "idle"
    TEACH = "teach"               # Recording mode
    SAVING = "saving"             # Saving files
    EXECUTE_STOPPED = "execute_stopped"
    EXECUTE_RUNNING = "execute_running"
    ERROR = "error"


class RobotStateNotifier:
    """
    Robot State Notifier - Plug and play visual feedback module.

    Usage:
        # Basic usage with auto port detection
        notifier = RobotStateNotifier()

        # Set states
        notifier.set_state(RobotState.TEACH)
        notifier.set_state(RobotState.SAVING)

        # With keyboard callback for recording toggle
        notifier.on_enter_pressed(my_callback)
        notifier.start_keyboard_listener()

        # Cleanup
        notifier.cleanup()

    States and Colors:
        IDLE:              CYAN (G+B)
        TEACH:             GREEN (recording)
        SAVING:            YELLOW (R+G)
        EXECUTE_STOPPED:   BLUE
        EXECUTE_RUNNING:   WHITE
        ERROR:             RED
    """

    def __init__(self, port: Optional[str] = None, auto_detect: bool = True):
        """
        Initialize the Robot State Notifier.

        Args:
            port: Serial port path. If None and auto_detect=True, will scan for USB ports.
            auto_detect: Whether to auto-detect USB port if port is None.
        """
        self._state = RobotState.IDLE
        self._lamp: Optional[USBLampController] = None
        self._keyboard: Optional[KeyboardListener] = None
        self._enter_callback: Optional[Callable] = None
        self._saving_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Resolve port
        if port is None and auto_detect:
            port = '/dev/ttyUSB1' 

        if port:
            self._lamp = USBLampController(port=port)
            self._set_color_for_state(self._state)
        else:
            print("[WARNING] No USB lamp port found, running in simulation mode")

    @staticmethod
    def _auto_detect_port() -> Optional[str]:
        """Auto-detect USB serial port."""
        patterns = [
            '/dev/ttyUSB*',
            '/dev/ttyACM*',
            '/dev/cu.usbserial*',
            '/dev/tty.usbserial*',
        ]

        for pattern in patterns:
            ports = glob.glob(pattern)
            if ports:
                return sorted(ports)[0]

        return None

    @property
    def state(self) -> RobotState:
        """Get current state."""
        return self._state

    def set_state(self, state: RobotState) -> None:
        """
        Set robot state and update lamp color.

        Args:
            state: The new robot state.
        """
        with self._lock:
            self._state = state
            self._set_color_for_state(state)

    def _set_color_for_state(self, state: RobotState) -> None:
        """Set lamp color based on state."""
        if self._lamp is None:
            print(f"[SIM] State: {state.value}")
            return

        color_map = {
            RobotState.IDLE: self._lamp.set_cyan,
            RobotState.TEACH: self._lamp.set_green,
            RobotState.SAVING: self._lamp.set_yellow,
            RobotState.EXECUTE_STOPPED: self._lamp.set_blue,
            RobotState.EXECUTE_RUNNING: self._lamp.set_white,
            RobotState.ERROR: self._lamp.set_red,
        }

        color_func = color_map.get(state)
        if color_func:
            color_func()

    # Convenience methods
    def idle(self) -> None:
        """Set state to IDLE (CYAN)."""
        self.set_state(RobotState.IDLE)

    def teach(self) -> None:
        """Set state to TEACH/RECORDING (GREEN)."""
        self.set_state(RobotState.TEACH)

    def recording(self) -> None:
        """Alias for teach() - Set state to RECORDING (GREEN)."""
        self.teach()

    def saving(self) -> None:
        """
        Set state to SAVING (YELLOW).

        Args:
            duration: If > 0, automatically return to IDLE after this duration.
            callback: Optional callback to execute after saving completes.
        """
        self.set_state(RobotState.SAVING)


    def execute_start(self) -> None:
        """Set state to EXECUTE_RUNNING (WHITE)."""
        self.set_state(RobotState.EXECUTE_RUNNING)

    def execute_stop(self) -> None:
        """Set state to EXECUTE_STOPPED (BLUE)."""
        self.set_state(RobotState.EXECUTE_STOPPED)

    def error(self) -> None:
        """Set state to ERROR (RED)."""
        self.set_state(RobotState.ERROR)

    # Keyboard integration
    def on_enter_pressed(self, callback: Callable) -> None:
        """
        Register callback for Enter key press.

        Args:
            callback: Function to call when Enter is pressed.
        """
        self._enter_callback = callback

    def _handle_enter(self) -> None:
        """Internal handler for Enter key."""
        if self._enter_callback:
            self._enter_callback()

    def start_keyboard_listener(self) -> None:
        """Start listening for keyboard events."""
        if self._keyboard is None:
            self._keyboard = KeyboardListener()

        self._keyboard.register_callback('enter', self._handle_enter)
        self._keyboard.start()

    def stop_keyboard_listener(self) -> None:
        """Stop listening for keyboard events."""
        if self._keyboard:
            self._keyboard.stop()

    def cleanup(self) -> None:
        """Cleanup resources."""
        self.stop_keyboard_listener()

        if self._lamp:
            self._lamp.turn_off_all()
            self._lamp.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


class RecordingController:
    """
    Recording Controller - Manages recording state with keyboard control.

    Usage:
        controller = RecordingController()
        controller.on_recording_start(start_recording_func)
        controller.on_recording_stop(stop_recording_func)
        controller.start()

        # Press Enter to toggle recording
        # Recording: GREEN -> SAVING (YELLOW) -> IDLE (CYAN)
    """

    def __init__(self, port: Optional[str] = None, saving_duration: float = 0.0):
        """
        Initialize Recording Controller.

        Args:
            port: USB lamp port. Auto-detect if None.
            saving_duration: Duration to show SAVING state (seconds).
        """
        self._notifier = RobotStateNotifier(port=port)
        self._is_recording = False
        self._saving_duration = saving_duration
        self._start_callback: Optional[Callable] = None
        self._stop_callback: Optional[Callable] = None
        self._lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording

    @property
    def notifier(self) -> RobotStateNotifier:
        """Get the underlying notifier."""
        return self._notifier

    def on_recording_start(self, callback: Callable) -> None:
        """Register callback for recording start."""
        self._start_callback = callback

    def on_recording_stop(self, callback: Callable) -> None:
        """Register callback for recording stop."""
        self._stop_callback = callback

    def _toggle_recording(self) -> None:
        """Toggle recording state (called by Enter key)."""
        with self._lock:
            if not self._is_recording:
                self._is_recording = True
                self._notifier.teach()
                if self._start_callback:
                    self._start_callback()
            else:
                self._is_recording = False
                if self._stop_callback:
                    self._stop_callback()
                self._notifier.saving(duration=self._saving_duration)

    def start(self) -> None:
        """Start the controller with keyboard listener."""
        self._notifier.on_enter_pressed(self._toggle_recording)
        self._notifier.start_keyboard_listener()
        self._notifier.idle()

    def stop(self) -> None:
        """Stop the controller."""
        self._notifier.cleanup()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
