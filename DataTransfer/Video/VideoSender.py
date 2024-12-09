import socket
import struct
import time

from PIL import Image

from DataTransfer.Video.Camera import Camera
from config import *
from util import compress_image


class VideoSender:
    def __init__(self, camera: Camera, socket_connection: socket.socket, client_id: str = None, frame_rate=30):
        self.camera = camera
        self.client_id = client_id.encode('utf-8') if client_id else b''
        self.frame_rate = frame_rate
        self.sock = socket_connection
        self._running = False

    def start(self):
        self._running = True
        client_id_len = len(self.client_id)
        while self._running:
            frame = self.camera.get_frame()
            if frame is None:
                continue
            # Resize the frame to the camera resolution
            frame: Image = frame.resize((camera_width, camera_height), Image.BILINEAR)
            compressed_data = compress_image(frame)
            data_len = len(compressed_data)
            # Send the data in chunks
            num_chunks = (data_len // VIDEO_CHUNK_SIZE) + 1
            sequence_number = 0
            for i in range(num_chunks):
                chunk = compressed_data[i * VIDEO_CHUNK_SIZE: (i + 1) * VIDEO_CHUNK_SIZE]
                self.sock.send(
                    struct.pack("I", client_id_len) + self.client_id +
                    struct.pack("Q", data_len) + struct.pack("I", sequence_number) + chunk)
                sequence_number += 1
            time.sleep(1.0 / self.frame_rate)

    def stop(self):
        self._running = False
        self.camera.stop()


    def terminate(self):
        self.stop()
        terminate_signal = (struct.pack("I", len(self.client_id))
                       + self.client_id + struct.pack("Q", 0) + struct.pack("I", 0))\
                       + b'TERMINATE'
        try:
             self.sock.send(terminate_signal)
        except OSError:
            pass
