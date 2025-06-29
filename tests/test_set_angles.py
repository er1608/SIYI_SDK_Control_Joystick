import sys
import os
from time import sleep
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from siyi_sdk import SIYISDK

def test():
    cam = SIYISDK(server_ip="192.168.144.25", port=37260)

    if not cam.connect():
        print("No connection ")
        exit(1)
    cam.requestHardwareID() # Important to get the angles limits defined in cameras.py
    sleep(1)
    target_yaw_deg = 45
    target_pitch_deg = 0
    cam.requestSetAngles(target_yaw_deg, target_pitch_deg)
    print("Attitude (yaw,pitch,roll) eg:", cam.getAttitude())

    print("Done and closing...")
    cam.disconnect()

if __name__ == "__main__":
    test()