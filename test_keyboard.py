#!/usr/bin/env python3
"""Test keyboard detection with lamp control."""

import sys
import time
from dataarm_notifier import USBLampController, KeyboardListener

# Use your lamp port
LAMP_PORT = '/dev/ttyUSB1'

def main():
    lamp = USBLampController(port=LAMP_PORT)
    listener = KeyboardListener()

    colors = ['red', 'green', 'blue']
    current_idx = [0]  # Use list for mutable closure

    def on_enter():
        color = colors[current_idx[0]]
        print(f"\nENTER pressed! Switching to {color.upper()}")

        if color == 'red':
            lamp.set_red()
        elif color == 'green':
            lamp.set_green()
        elif color == 'blue':
            lamp.set_blue()

        current_idx[0] = (current_idx[0] + 1) % len(colors)

    listener.register_callback('enter', on_enter)

    print("=" * 50)
    print("Keyboard + Lamp Test")
    print("=" * 50)
    print(f"Lamp port: {LAMP_PORT}")
    print("Press ENTER to cycle colors (red -> green -> blue)")
    print("Press Ctrl+C to exit")
    print("=" * 50)

    try:
        listener.start()
        print("\nKeyboard listener started! Press ENTER...")
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        listener.stop()
        lamp.turn_off_all()
        print("Done!")

if __name__ == "__main__":
    main()
