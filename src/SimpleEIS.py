import cv2
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import numpy as np
import subprocess
import time
import threading
import queue
import os
import sys
import datetime

def restart_script():
    print(f"restart")
    python = sys.executable
    os.execl(python, python, *sys.argv)

Gst.init(None)

RTSP_URL = 'rtsp://192.168.144.25:8554/main.264'
RES = (1280, 720)
FPS = 20

frame_queue = queue.Queue(maxsize=5)

ffmpeg = subprocess.Popen([
    'ffmpeg',
    '-loglevel', 'quiet',
    '-y',
    '-f', 'rawvideo',
    '-vcodec', 'rawvideo',
    '-pix_fmt', 'bgr24',
    '-s', f'{RES[0]}x{RES[1]}',
    '-r', str(FPS),
    '-i', '-',
    '-flush_packets', '1',
    '-probesize', '32',
    '-analyzeduration', '0',
    '-an',
    '-c:v', 'libx264',
    '-preset', 'ultrafast',
    '-tune', 'zerolatency',
    '-f', 'rtp',
    'rtp://127.0.0.1:5600'
], stdin=subprocess.PIPE)

pipeline_str = (
    f"rtspsrc location={RTSP_URL} latency=0 protocols=tcp ! "
    "rtph264depay ! h264parse ! avdec_h264 ! "
    f"videoscale ! videoconvert ! video/x-raw,width={RES[0]},height={RES[1]},format=BGR ! appsink name=sink emit-signals=true sync=false max-buffers=1 drop=true"
)

pipeline = Gst.parse_launch(pipeline_str)
appsink = pipeline.get_by_name("sink")
pipeline.set_state(Gst.State.PLAYING)

class SimpleEIS:
    def __init__(self):
        self.prev_gray = None
        self.transforms = []

    def stabilize(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.prev_gray is None:
            self.prev_gray = gray
            return frame

        prev_pts = cv2.goodFeaturesToTrack(self.prev_gray, maxCorners=200, qualityLevel=0.01, minDistance=30)
        next_pts, status, _ = cv2.calcOpticalFlowPyrLK(self.prev_gray, gray, prev_pts, None)

        good_prev = prev_pts[status.flatten() == 1]
        good_next = next_pts[status.flatten() == 1]

        m = cv2.estimateAffinePartial2D(good_prev, good_next)[0]
        if m is None:
            return frame

        stabilized = cv2.warpAffine(frame, m, (frame.shape[1], frame.shape[0]),
                                    flags=cv2.INTER_LINEAR,
                                    borderMode=cv2.BORDER_REFLECT)

        self.prev_gray = gray
        return stabilized

stabilizer = SimpleEIS()

def center_crop(frame, size=(1280, 720)):
    h, w = frame.shape[:2]
    ch, cw = size[1], size[0]
    start_x = max((w - cw) // 2, 0)
    start_y = max((h - ch) // 2, 0)
    return frame[start_y:start_y + ch, start_x:start_x + cw]

def read_and_stabilize():
    while True:
        sample = appsink.emit("pull-sample")
        if sample is None:
            time.sleep(0.005)
            continue

        buf = sample.get_buffer()
        caps = sample.get_caps()
        width = caps.get_structure(0).get_value("width")
        height = caps.get_structure(0).get_value("height")

        success, mapinfo = buf.map(Gst.MapFlags.READ)
        if not success:
            continue

        frame = np.frombuffer(mapinfo.data, dtype=np.uint8).reshape((height, width, 3))
        buf.unmap(mapinfo)
        
        stabilized = stabilizer.stabilize(frame)
        stabilized_copy = stabilized.copy()
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        cv2.putText(stabilized_copy, timestamp, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if stabilized is not None:
            cropped = center_crop(stabilized_copy, RES)

            try:
                frame_queue.put_nowait(cropped)
            except queue.Full:
                pass

def write_to_ffmpeg():
    last_write_time = time.time()
    while True:
        now = time.time()
        if now - last_write_time > 3:
            restart_script()
        
        try:
            start_eis = time.time()
            frame = frame_queue.get(timeout=1)
            ffmpeg.stdin.write(frame.tobytes())
            last_write_time = time.time()
            eis_ts = time.time()
            print(f"⏱️ EIS mất: {(eis_ts - start_eis)*1000:.2f} ms")
        except queue.Empty:
            continue

print("Đang stream và ổn định video... Nhấn Ctrl+C để dừng.")

try:
    t1 = threading.Thread(target=read_and_stabilize, daemon=True)
    t2 = threading.Thread(target=write_to_ffmpeg, daemon=True)

    t1.start()
    t2.start()

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Dừng lại bởi người dùng.")

finally:
    pipeline.set_state(Gst.State.NULL)
    ffmpeg.stdin.close()
    ffmpeg.wait()

