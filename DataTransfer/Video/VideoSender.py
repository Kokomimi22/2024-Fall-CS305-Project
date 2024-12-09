import socket
import struct
import time

import cv2
import ffmpeg
import numpy as np

from DataTransfer.Video.Camera import Camera
from config import *


class VideoSender:
    def __init__(self, camera: Camera, socket_connection: socket.socket, client_id: str=None, frame_rate=30):
        self.camera = camera
        self.client_id = client_id.encode('utf-8') if client_id else b''
        self.frame_rate = frame_rate
        self.sock = socket_connection
        self._running = False

    def start(self):
        self._running = True
        client_id_len = len(self.client_id)
        while self._running:
            ret, frame = self.camera.get_frame()
            if not ret:
                continue
            # 调整帧的分辨率
            frame = cv2.resize(frame, (camera_width, camera_height))
            # Encode the frame using ffmpeg
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_bytes = np.array(frame_rgb).tobytes()
            process = (
                ffmpeg
                .input('pipe:0', format='rawvideo', pix_fmt='rgb24', s=f'{frame.shape[1]}x{frame.shape[0]}')
                .output('pipe:1', format='h264')
                .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
            )
            out, _ = process.communicate(input=frame_bytes)
            data_len = len(out)
            # Send the frame data in chunks
            num_chunks = (data_len // VIDEO_CHUNK_SIZE) + 1
            sequence_number = 0
            for i in range(num_chunks):
                chunk = out[i * VIDEO_CHUNK_SIZE: (i + 1) * VIDEO_CHUNK_SIZE]
                packet = (struct.pack("I", client_id_len) +
                          self.client_id + struct.pack("Q", data_len) +
                          struct.pack("I", sequence_number) +
                          struct.pack("d", time.time()) +
                          chunk)
                self.sock.send(packet)
                sequence_number += 1
            time.sleep(1.0 / self.frame_rate)

    def stop(self):
        self._running = False
        self.camera.stop()

    def terminate(self):
        self.stop()
        terminate_signal = struct.pack("I", len(self.client_id)) + self.client_id + struct.pack("Q", 0) + struct.pack("I", 0) + b'TERMINATE'
        try:
            self.sock.send(terminate_signal)
        except OSError:
            pass