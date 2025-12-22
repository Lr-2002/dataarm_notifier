"""
Color Cycle Controller - combines keyboard listener with lamp controller.

This module provides an easy-to-use controller that listens for Enter key presses
and automatically cycles through colors (red, green, blue) on a USB lamp.
"""

import threading
import time
from typing import Optional
from dataclasses import dataclass

from .usb_lamp_controller import USBLampController
from .keyboard_listener import KeyboardListener


@dataclass
class ColorCycleConfig:
    """Configuration for color cycling."""
    colors: list = None
    cycle_interval: float = 2.0  # seconds between automatic cycles

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.colors is None:
            self.colors = ['red', 'green', 'blue']


class ColorCycleController:
    """
    Controls color cycling on a USB lamp based on keyboard input.

    This class integrates keyboard listening with lamp control to provide
    an easy way to cycle through colors by pressing Enter.
    """

    def __init__(self,
                 port: str,
                 config: Optional[ColorCycleConfig] = None,
                 auto_start: bool = False):
        """
        Initialize the color cycle controller.

        Args:
            port: Serial port for the USB lamp (e.g., '/dev/cu.usbserial-1330')
            config: Configuration for color cycling
            auto_start: If True, automatically start listening on initialization
        """
        self.port = port
        self.config = config or ColorCycleConfig()
        self._lamp: Optional[USBLampController] = None
        self._keyboard_listener = KeyboardListener()
        self._current_color_index = 0
        self._auto_cycle = False
        self._auto_cycle_thread: Optional[threading.Thread] = None
        self._running = False
        self._keyboard_available = False  # Track if keyboard monitoring works
        self._lock = threading.Lock()

        # Register callback for Enter key
        self._keyboard_listener.register_callback('enter', self._on_enter_pressed)

    def start(self):
        """Start the color cycle controller."""
        with self._lock:
            if self._running:
                return

            # Initialize lamp
            self._lamp = USBLampController(port=self.port)
            self._lamp.connect()

            # Check keyboard availability and start listening
            try:
                self._keyboard_listener.start()

                # Check if keyboard is actually working
                if not self._keyboard_listener.is_listening():
                    print("⚠️  Keyboard monitoring not available")
                    print("💡 Will use manual commands instead")
                    self._keyboard_available = False
                else:
                    print("🎨 Color Cycle Controller started!")
                    print("📌 Press ENTER to switch to next color")
                    self._keyboard_available = True
            except (OSError, RuntimeError) as e:
                print(f"⚠️  Keyboard monitoring unavailable: {e}")
                print("💡 Will use manual commands instead")
                self._keyboard_available = False

            print("📌 Press Ctrl+C to stop")
            self._running = True

    def stop(self):
        """Stop the color cycle controller."""
        with self._lock:
            if not self._running:
                return

            # Stop auto cycling
            self.stop_auto_cycle()

            # Stop keyboard listening
            self._keyboard_listener.stop()

            # Close lamp connection
            if self._lamp:
                self._lamp.turn_off_all()
                self._lamp.close()
                self._lamp = None

            self._running = False
            print("\n🎨 Color Cycle Controller stopped!")

    def _on_enter_pressed(self):
        """Handle Enter key press."""
        self.next_color()

    def next_color(self):
        """Switch to the next color in the cycle."""
        with self._lock:
            if not self._running or not self._lamp:
                return

            # Turn off all lights first
            self._lamp.turn_off_all()
            time.sleep(0.1)

            # Move to next color
            self._current_color_index = (self._current_color_index + 1) % len(self.config.colors)
            current_color = self.config.colors[self._current_color_index]

            # Turn on the new color
            if current_color == 'red':
                self._lamp.set_red(on=True)
                print(f"🔴 Switched to RED")
            elif current_color == 'green':
                self._lamp.set_green(on=True)
                print(f"🟢 Switched to GREEN")
            elif current_color == 'blue':
                self._lamp.set_blue(on=True)
                print(f"🔵 Switched to BLUE")

    def set_color(self, color: str):
        """
        Set a specific color.

        Args:
            color: Color to set ('red', 'green', 'blue')
        """
        with self._lock:
            if not self._running or not self._lamp:
                return

            color = color.lower()
            if color not in self.config.colors:
                print(f"❌ Invalid color: {color}. Valid colors: {self.config.colors}")
                return

            # Turn off all lights
            self._lamp.turn_off_all()
            time.sleep(0.1)

            # Update current index
            self._current_color_index = self.config.colors.index(color)

            # Turn on the specified color
            if color == 'red':
                self._lamp.set_red(on=True)
                print(f"🔴 Set to RED")
            elif color == 'green':
                self._lamp.set_green(on=True)
                print(f"🟢 Set to GREEN")
            elif color == 'blue':
                self._lamp.set_blue(on=True)
                print(f"🔵 Set to BLUE")

    def start_auto_cycle(self, interval: Optional[float] = None):
        """
        Start automatic color cycling.

        Args:
            interval: Time between color changes in seconds (uses config default if None)
        """
        with self._lock:
            if self._auto_cycle:
                return

            cycle_interval = interval or self.config.cycle_interval
            self._auto_cycle = True
            self._auto_cycle_thread = threading.Thread(
                target=self._auto_cycle_loop,
                args=(cycle_interval,),
                daemon=True
            )
            self._auto_cycle_thread.start()
            print(f"🔄 Auto cycle started (interval: {cycle_interval}s)")

    def stop_auto_cycle(self):
        """Stop automatic color cycling."""
        with self._lock:
            self._auto_cycle = False
            if self._auto_cycle_thread and self._auto_cycle_thread.is_alive():
                self._auto_cycle_thread.join(timeout=1.0)
            self._auto_cycle_thread = None
            print("⏹️ Auto cycle stopped")

    def _auto_cycle_loop(self, interval: float):
        """Internal loop for automatic color cycling."""
        while self._auto_cycle:
            time.sleep(interval)
            if self._auto_cycle:
                self.next_color()

    def turn_off_all(self):
        """Turn off all lights."""
        with self._lock:
            if self._lamp:
                self._lamp.turn_off_all()
                print("⚫ All lights turned off")

    def get_current_color(self) -> Optional[str]:
        """
        Get the current active color.

        Returns:
            Current color name or None
        """
        with self._lock:
            if not self._running:
                return None
            return self.config.colors[self._current_color_index]

    def is_running(self) -> bool:
        """
        Check if the controller is running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    def is_auto_cycle_active(self) -> bool:
        """
        Check if auto cycling is active.

        Returns:
            True if auto cycling, False otherwise
        """
        return self._auto_cycle

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
