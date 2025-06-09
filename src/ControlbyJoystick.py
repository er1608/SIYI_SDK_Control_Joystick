import pyjoystick
from pyjoystick.sdl2 import Key, run_event_loop
import socket
import sys
import os
from time import sleep
import time
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

yaw = 0
pitch = 0
last_yaw = 0
last_pitch = 0

from siyi_sdk import SIYISDK

cam = SIYISDK(server_ip="192.168.144.25", port=37260)

if not cam.connect():
    print("No connection ")
    exit(1)

cam.requestHardwareID()

def limit(val, min_val, max_val):
    return max(min(val, max_val), min_val)

def handle_key_event(key):
    start = time.perf_counter()

    global yaw, pitch, last_yaw, last_pitch

    if key.keytype == Key.AXIS:
        if key.number == 0:
            # yaw = int(key.value * 135)
            yaw += int(key.value * 5)

        elif key.number == 1:
            # pitch = int(key.value * 90)
            pitch += int(key.value * 5)

    elif key.keytype == Key.HAT:  
        if key.value == 1:
            pitch += 5
        elif key.value == 4:
            pitch -= 5
        elif key.value == 8:
            yaw -= 5
        elif key.value == 2:
            yaw += 5     

    yaw = limit(yaw, -135, 135)
    pitch = limit(pitch, -90, 25)

    if abs(yaw - last_yaw) > 2 or abs(pitch - last_pitch) > 2:
        cam.requestSetAngles(yaw, pitch)

        last_yaw = yaw
        last_pitch = pitch

        print(f"Joystick: yaw={yaw}, pitch={pitch}")

    end = time.perf_counter() - start
    print('{:.6f}s for the calculation'.format(end))

# Loop to check joystick
repeater = pyjoystick.HatRepeater(first_repeat_timeout=0.5, repeat_timeout=0.03, check_timeout=0.01)
mngr = pyjoystick.ThreadEventManager(
    event_loop=run_event_loop,
    handle_key_event=handle_key_event,
    button_repeater=repeater
)

mngr.start()

try:
    input("Connected! Press Enter to exit.\n")
finally:
    mngr.stop()
    cam.disconnect()
    print("Disconnected to the camera.")
