"""
Mock keyboard listener for environments where keyboard module doesn't work.

This is a fallback implementation that uses stdin instead of system keyboard events.
"""

import threading
import time
import sys
from typing import Callable, Optional

# Check if real keyboard is available
try:
    import keyboard as real_keyboard
    KEYBOARD_AVAILABLE = True
except:
    KEYBOARD_AVAILABLE = False


class KeyboardListener:
    """
    A keyboard listener that runs in a separate thread.

    This is a mock implementation that works without system-level keyboard access.
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
            key: The key to listen for ('enter', 'a', etc.)
            callback: Function to call when the key is pressed
        """
        with self._lock:
            self._callbacks[key.lower()] = callback

    def unregister_callback(self, key: str):
        """Unregister a callback for a specific key."""
        with self._lock:
            self._callbacks.pop(key.lower(), None)

    def _keyboard_event_handler(self, event):
        """Internal handler for keyboard events."""
        # Mock implementation - in real usage, this would handle events
        pass

    def start(self):
        """Start listening for keyboard events."""
        if not KEYBOARD_AVAILABLE:
            print("⚠️  Using MOCK keyboard listener (stdin-based)")
            print("   (Real keyboard monitoring requires special permissions on macOS)")
            print("   Press keys followed by Enter to trigger callbacks")
            print()

        if self._listening:
            return

        self._listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def _listen_loop(self):
        """Main listening loop running in a separate thread."""
        if not KEYBOARD_AVAILABLE:
            # Use stdin for mock implementation
            self._mock_listen_loop()
        else:
            # Use real keyboard module
            try:
                real_keyboard.hook(self._keyboard_event_handler)
                while self._listening:
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error in keyboard listener: {e}")
            finally:
                real_keyboard.unhook_all()

    def _mock_listen_loop(self):
        """Mock listening using stdin."""
        try:
            while self._listening:
                # Use stdin with timeout
                import select
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    line = sys.stdin.readline().strip().lower()
                    if line:
                        with self._lock:
                            callback = self._callbacks.get(line)
                        if callback:
                            callback()
                        elif line == 'quit' or line == 'exit':
                            break
        except Exception as e:
            print(f"Mock keyboard error: {e}")

    def stop(self):
        """Stop listening for keyboard events."""
        self._listening = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def is_listening(self) -> bool:
        """Check if the listener is currently active."""
        return self._listening

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
