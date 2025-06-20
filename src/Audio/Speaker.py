import socket
import pyaudio

CHUNK = 1024
PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', PORT))

print("⏳ Đang chờ metadata...")

# Nhận metadata an toàn
while True:
    meta_data, _ = sock.recvfrom(1024)
    try:
        meta_text = meta_data.decode()
        if meta_text.startswith("META|"):
            _, rate, channels, sampwidth = meta_text.split("|")
            rate = int(rate)
            channels = int(channels)
            sampwidth = int(sampwidth)
            break
    except UnicodeDecodeError:
        continue

print(f"📥 Định dạng nhận được: {channels} kênh, {sampwidth*8}-bit, {rate}Hz")

p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(sampwidth),
                channels=channels,
                rate=rate,
                output=True)

print("▶️ Bắt đầu nhận và phát âm thanh...")

try:
    while True:
        data, _ = sock.recvfrom(4096)
        stream.write(data)
except KeyboardInterrupt:
    print("🛑 Kết thúc.")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    sock.close()
