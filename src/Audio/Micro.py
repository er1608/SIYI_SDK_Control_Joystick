import socket
import pyaudio
import time
import struct
import math

CHUNK = 1024
RATE = 48000
CHANNELS = 1
SAMPLE_WIDTH = 2

IP = '192.168.144.100'  # IP bên receiver
PORT = 5005

# Khởi tạo socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Gửi metadata 1 lần
meta = f"META|{RATE}|{CHANNELS}|{SAMPLE_WIDTH}"
sock.sendto(meta.encode(), (IP, PORT))
time.sleep(0.1)

def rms(data):
    count = len(data) // 2 
    fmt = f"{count}h"
    shorts = struct.unpack(fmt, data)
    sum_squares = sum(s**2 for s in shorts)
    return math.sqrt(sum_squares / count)

# Khởi tạo PyAudio để ghi âm từ mic
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,  # 16-bit = 2 bytes
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print(f"🎤 Streaming microphone to {IP}:{PORT}... (Press Ctrl+C to stop)")

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)

        volume = rms(data)
        if volume > 500:
            print(f"🎙️ Voice activity detected (RMS={volume:.1f})")

        sock.sendto(data, (IP, PORT))
except KeyboardInterrupt:
    print("🛑 Stopped.")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    sock.close()