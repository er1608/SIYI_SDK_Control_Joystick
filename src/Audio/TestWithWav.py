import socket
import wave
import time

CHUNK = 1024
IP = '192.168.144.100'
PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
wf = wave.open('voice.wav', 'rb')

# Gửi metadata duy nhất 1 lần
meta = f"META|{wf.getframerate()}|{wf.getnchannels()}|{wf.getsampwidth()}"
sock.sendto(meta.encode(), (IP, PORT))
time.sleep(0.1)

# Gửi dữ liệu âm thanh
while True:
    data = wf.readframes(CHUNK)
    if not data:
        break
    sock.sendto(data, (IP, PORT))
    print(f"Sent {len(data)} bytes to {IP}:{PORT}")
    time.sleep(CHUNK / wf.getframerate())

wf.close()
sock.close()
