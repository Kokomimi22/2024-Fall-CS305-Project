import time
import cv2
import socket
import struct
import zlib
from config import *

class VideoSender:
    def __init__(self, camera, dest_addr, client_id: str = None, compression_level=3, frame_rate=30):
        self.camera = camera
        self.dest_addr = dest_addr
        self.client_id = client_id.encode('utf-8') if client_id else b''
        self.compression_level = compression_level
        self.frame_rate = frame_rate
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = False

    def start(self):
        self.running = True
        client_id_len = len(self.client_id)
        while self.running:
            frame = self.camera.get_frame()
            if frame is None:
                continue
            frame = cv2.resize(frame, (camera_width, camera_height))
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            compressed_data = zlib.compress(buffer, self.compression_level)
            data_len = len(compressed_data)
            num_chunks = (data_len // VIDEO_CHUNK_SIZE) + 1
            sequence_number = 0
            for i in range(num_chunks):
                chunk = compressed_data[i * VIDEO_CHUNK_SIZE: (i + 1) * VIDEO_CHUNK_SIZE]
                self.sock.sendto(
                    struct.pack("I", client_id_len) + self.client_id +
                    struct.pack("Q", data_len) + struct.pack("I", sequence_number) + chunk,
                    self.dest_addr
                )
                sequence_number += 1
            time.sleep(1.0 / self.frame_rate)
        self.sock.close()

    def stop(self):
        self.running = False