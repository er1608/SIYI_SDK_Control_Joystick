import asyncio
import pygame
import sys
import os
import time

from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw, VelocityBodyYawspeed)
# Import SIYI SDK
from siyi_sdk import SIYISDK

# Init SIYI camera
# cam = SIYISDK(server_ip="192.168.144.25", port=37260)

# if not cam.connect():
#     print("Can not connect SIYI camera.")
#     sys.exit(1)

# cam.requestHardwareID()

def limit(val, min_val, max_val):
    return max(min(val, max_val), min_val)

async def run():
    # Camera params
    camera_yaw = 0
    camera_pitch = 0
    last_yaw = 0
    last_pitch = 0

    # UAV params
    UAVX = 0
    UAVY = 0
    temp = 0
    
    # control_mode: 0 (yaw & altitude); 1 (camera)
    control_mode = 0

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("There is no joystick!")
        sys.exit(1)

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Joystick connected: {joystick.get_name()}")

    clock = pygame.time.Clock()

    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    try:
        while True:
            UAV_Yaw = 0
            UAV_Altitude = 0

            # start = time.perf_counter()
            pygame.event.pump()  # Update joystick state

            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN and event.button == 1:
                    if control_mode == 0:
                        print(f"CHANGE BUTTON TO CONTROL CAMERA")
                        control_mode = 1
                    else:
                        print(f"CHANGE BUTTON TO CONTROL YAW & ALTITUDE")
                        control_mode = 0

                if event.type == pygame.JOYBUTTONDOWN and event.button == 2:
                    print(f"ARMING")
                    temp = 1

                if event.type == pygame.JOYBUTTONDOWN and event.button == 3:
                    print(f"LANDING")
                    temp = 3

                if event.type == pygame.JOYBUTTONDOWN and event.button == 5:
                    print(f"RETURN TO LAUNCH")
                    temp = 4

            if control_mode == 1:
                hat_x, hat_y = joystick.get_hat(0)
                if hat_y == 1:
                    camera_pitch -= 5
                elif hat_y == -1:
                    camera_pitch += 5
                if hat_x == 1:
                    camera_yaw += 5
                elif hat_x == -1:
                    camera_yaw -= 5

                # Angle limitation
                camera_yaw = limit(camera_yaw, -135, 135)
                camera_pitch = limit(camera_pitch, -90, 25)

                # Send command
                if abs(camera_yaw - last_yaw) > 2 or abs(camera_pitch - last_pitch) > 2:
                    # cam.requestSetAngles(yaw, pitch)
                    last_yaw = camera_yaw
                    last_pitch = camera_pitch
                    print(f"Sending: yaw={camera_yaw}, pitch={camera_pitch}")

            else:
                hat_x, hat_y = joystick.get_hat(0)
                if hat_y == 1:
                    # UAV_Altitude -= 0.1
                    UAV_Altitude = -10

                elif hat_y == -1:
                    # UAV_Altitude += 0.1
                    UAV_Altitude = 10

                if hat_x == 1:
                    # UAV_Yaw += 5
                    UAV_Yaw = 45.0

                elif hat_x == -1:
                    # UAV_Yaw -= 5
                    UAV_Yaw = -45.0

            axis_0 = joystick.get_axis(0)  # Yaw (X)
            axis_1 = joystick.get_axis(1)  # Pitch (Y)

            UAVX = -axis_1 * 2.0
            UAVY = axis_0 * 2.0

            # UAVX -= axis_1 * 0.1
            # UAVY += axis_0 * 0.1

            # X: North(North (+) / South (−))
            # Y: East(East (+) / West (−)) 
            # Z: Down (Down (+) / Up (−))

            # Position(north, east, down, yaw)
            # await drone.offboard.set_position_ned(PositionNedYaw(UAVX, UAVY, UAV_Altitude, UAV_Yaw))

            # print(f"Temp: {temp}")
            if temp == 0:
                continue

            elif temp == 1:
                print("Waiting for drone to have a global position estimate...")
                async for health in drone.telemetry.health():
                    if (health.is_global_position_ok and health.is_home_position_ok):
                            
                        print("-- Global position estimate OK")

                        await drone.action.hold()

                        await drone.action.arm()

                        print("-- Setting initial setpoint")
                        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))

                        print("-- Starting offboard")
                        try:
                            await drone.offboard.start()

                        except OffboardError as error:
                            print(f"Starting offboard mode failed \
                                    with error code: {error._result.result}")
                            print("-- Disarming")
                            await drone.action.disarm()

                            return

                        temp = 2

                        break
            
            elif temp == 2:
                await drone.offboard.set_velocity_body(VelocityBodyYawspeed(UAVX, UAVY, UAV_Altitude, UAV_Yaw))

            elif temp == 3:
                await drone.action.land() 
                temp = 0

            elif temp == 4:
                await drone.action.return_to_launch()
                temp = 0          

            # elapsed = time.perf_counter() - start
            # print(f"{elapsed:.6f}s for processing")

            clock.tick(20)  # 20 Hz

    except KeyboardInterrupt:
        print("\nSTOP CONTROL (Ctrl+C).")

    finally:
        pygame.quit()
        # cam.disconnect()
        print("CAMERA DISCONNECTED.")

        print("-- Stopping offboard")

        try:
            await drone.offboard.stop()

        except OffboardError as error:
            print(f"Stopping offboard mode failed \
                    with error code: {error._result.result}")
            return

if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())