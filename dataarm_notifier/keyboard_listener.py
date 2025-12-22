"""
Keyboard listener for detecting key presses.

This module provides a cross-platform keyboard listener that can detect
key presses in a separate thread, making it suitable for integration into
larger systems.
"""

import threading
import time
from typing import Callable, Optional
import sys

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except (ImportError, OSError, AttributeError, RuntimeError) as e:
    KEYBOARD_AVAILABLE = False
    # Store the error for debugging
    _keyboard_error = e
    # Don't print warning here, let the controller handle it gracefully


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
        self._thread: Optional[threading.Thread] = None
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

    def _keyboard_event_handler(self, event):
        """
        Internal handler for keyboard events.

        Args:
            event: keyboard event object
        """
        if event.event_type == keyboard.KEY_DOWN:
            key_name = event.name.lower()
            with self._lock:
                callback = self._callbacks.get(key_name)
            if callback:
                callback()

    def start(self):
        """Start listening for keyboard events."""
        if not KEYBOARD_AVAILABLE:
            raise RuntimeError("keyboard module not available. Install with: pip install keyboard")

        if self._listening:
            return

        self._listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def _listen_loop(self):
        """Main listening loop running in a separate thread."""
        try:
            keyboard.hook(self._keyboard_event_handler)
            while self._listening:
                time.sleep(0.1)
        except Exception as e:
            print(f"Error in keyboard listener: {e}")
        finally:
            keyboard.unhook_all()

    def stop(self):
        """Stop listening for keyboard events."""
        self._listening = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

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
