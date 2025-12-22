"""
Keyboard listener for detecting key presses.

This module provides a cross-platform keyboard listener that can detect
key presses in a separate thread, making it suitable for integration into
larger systems.

Uses pynput which works without root on X11/Wayland.
"""

import threading
from typing import Callable, Optional

try:
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except (ImportError, OSError, AttributeError, RuntimeError) as e:
    KEYBOARD_AVAILABLE = False
    _keyboard_error = e


class KeyboardListener:
    """
    A keyboard listener that runs in a separate thread.

    This class monitors keyboard input and calls registered callback functions
    when specific keys are pressed. It runs independently and can be easily
    integrated into other systems.
    """

    def __init__(self):
        """Initialize the keyboard listener."""
        self._listening = False
        self._listener: Optional[keyboard.Listener] = None
        self._callbacks = {}
        self._lock = threading.Lock()

    def register_callback(self, key: str, callback: Callable):
        """
        Register a callback function for a specific key.

        Args:
            key: The key to listen for (e.g., 'enter', 'space', 'a')
            callback: Function to call when the key is pressed
        """
        with self._lock:
            self._callbacks[key.lower()] = callback

    def unregister_callback(self, key: str):
        """
        Unregister a callback for a specific key.

        Args:
            key: The key to stop listening for
        """
        with self._lock:
            self._callbacks.pop(key.lower(), None)

    def _on_press(self, key):
        """
        Internal handler for key press events.

        Args:
            key: pynput key object
        """
        try:
            # Handle special keys (like Enter, Space, etc.)
            if hasattr(key, 'name'):
                key_name = key.name.lower()
            # Handle regular character keys
            elif hasattr(key, 'char') and key.char:
                key_name = key.char.lower()
            else:
                return

            with self._lock:
                callback = self._callbacks.get(key_name)
            if callback:
                callback()
        except Exception as e:
            print(f"Error in key handler: {e}")

    def start(self):
        """Start listening for keyboard events."""
        if not KEYBOARD_AVAILABLE:
            raise RuntimeError("pynput module not available. Install with: pip install pynput")

        if self._listening:
            return

        self._listening = True
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()

    def stop(self):
        """Stop listening for keyboard events."""
        self._listening = False
        if self._listener:
            self._listener.stop()
            self._listener = None

    def is_listening(self) -> bool:
        """
        Check if the listener is currently active.

        Returns:
            True if listening, False otherwise
        """
        return self._listening

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
