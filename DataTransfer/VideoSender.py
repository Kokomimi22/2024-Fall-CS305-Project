import time

import cv2
import socket
import struct
import zlib
from config import *
class VideoSender:
    def __init__(self, host, port, dest_addr, compression_level=3, frame_rate=30):
        self.host = host
        self.port = port
        self.dest_addr = dest_addr
        self.compression_level = compression_level
        self.frame_rate = frame_rate
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)

    def start(self):

        while True:
            ret, frame = self.cap.read()
            frame = cv2.resize(frame, (camera_width, camera_height))
            if not ret:
                break
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            compressed_data = zlib.compress(buffer, self.compression_level)
            data_len = len(compressed_data)
            num_chunks = (data_len // VIDEO_CHUNK_SIZE) + 1
            sequence_number = 0
            for i in range(num_chunks):
                chunk = compressed_data[i * VIDEO_CHUNK_SIZE : (i + 1) * VIDEO_CHUNK_SIZE]
                self.sock.sendto(struct.pack("Q", data_len) + struct.pack("I", sequence_number) + chunk, self.dest_addr)
                sequence_number += 1
            # 帧率不要太高，否则会导致数据包丢失，因为我的接收端并没有做类似于TCP的ACK机制
            time.sleep(1.0 / self.frame_rate)
        self.cap.release()
        self.sock.close()