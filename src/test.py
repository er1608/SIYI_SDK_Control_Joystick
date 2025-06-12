import pygame
import sys
import os
import time

# Import SIYI SDK
from siyi_sdk import SIYISDK

# =====================
# Khởi tạo camera SIYI
# =====================
cam = SIYISDK(server_ip="192.168.144.25", port=37260)

if not cam.connect():
    print("Không thể kết nối camera SIYI.")
    sys.exit(1)

cam.requestHardwareID()

# =====================
# Biến điều khiển
# =====================
yaw = 0
pitch = 0
last_yaw = 0
last_pitch = 0

def limit(val, min_val, max_val):
    return max(min(val, max_val), min_val)

# =====================
# Khởi tạo pygame
# =====================
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("Không tìm thấy joystick!")
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Đã kết nối joystick: {joystick.get_name()}")

# =====================
# Vòng lặp chính
# =====================
clock = pygame.time.Clock()

try:
    while True:
        start = time.perf_counter()
        pygame.event.pump()  # Cập nhật trạng thái joystick

        # Axis: trục chính
        axis_0 = joystick.get_axis(0)  # Yaw (X)
        axis_1 = joystick.get_axis(1)  # Pitch (Y)

        # Điều chỉnh góc theo trục
        yaw += int(axis_0 * 5)
        pitch += int(axis_1 * 5)

        # D-pad (Hat)
        hat_x, hat_y = joystick.get_hat(0)
        if hat_y == 1:
            pitch -= 5
        elif hat_y == -1:
            pitch += 5
        if hat_x == 1:
            yaw += 5
        elif hat_x == -1:
            yaw -= 5

        # Giới hạn góc
        yaw = limit(yaw, -135, 135)
        pitch = limit(pitch, -90, 25)

        # Gửi lệnh nếu thay đổi đáng kể
        if abs(yaw - last_yaw) > 2 or abs(pitch - last_pitch) > 2:
            cam.requestSetAngles(yaw, pitch)
            last_yaw = yaw
            last_pitch = pitch
            print(f"Gửi: yaw={yaw}, pitch={pitch}")

        elapsed = time.perf_counter() - start
        print(f"{elapsed:.6f}s để xử lý")

        clock.tick(20)  # 20 Hz
except KeyboardInterrupt:
    print("\nDừng điều khiển (Ctrl+C).")
finally:
    pygame.quit()
    cam.disconnect()
    print("Đã ngắt kết nối camera.")
