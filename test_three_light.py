import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import time
from usb_lamp_controller import USBLampController
lamp = USBLampController()
lamp.set_red()

time.sleep(1)
lamp.set_blue()

time.sleep(1)
lamp.set_green()

time.sleep(1)
lamp.turn_off_all()
