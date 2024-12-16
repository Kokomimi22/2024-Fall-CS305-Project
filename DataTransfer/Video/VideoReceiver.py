import math
import socket
import struct
import threading

import cv2
import ffmpeg
import numpy as np

from config import *
from util import overlay_camera_images


class VideoReceiver:
    def __init__(self, socket_connection: socket.socket):
        self.sock = socket_connection
        self.sock.setblocking(False)
        self.buffers = {}  # Dictionary to store buffers for each client
        self.expected_sequences = {}  # Dictionary to store expected sequences for each client
        self.received_chunks = {}  # Dictionary to store received chunks for each client
        self.frames = {}  # Dictionary to store last frames for each client
        self._running = False

    @staticmethod
    def _unpack_data(data):
        offset = 0
        client_id_len = struct.unpack_from("I", data, offset)[0]
        offset += struct.calcsize("I")
        client_id = data[offset:offset + client_id_len].decode('utf-8')
        offset += client_id_len
        data_len = struct.unpack_from("Q", data, offset)[0]
        offset += struct.calcsize("Q")
        sequence_number = struct.unpack_from("I", data, offset)[0]
        offset += struct.calcsize("I")
        chunk_data = data[offset:]
        return client_id, data_len, sequence_number, chunk_data

    def start(self):
        self._running = True
        while self._running:
            try:
                data, _ = self.sock.recvfrom(65536)
                if data == b'Cancelled':
                    break
            except BlockingIOError:
                continue
            except ConnectionResetError:
                print("Connection reset by the server")
                break
            client_id, data_len, sequence_number, chunk_data = self._unpack_data(data)
            if chunk_data == b'TERMINATE':
                self.remove_client(client_id)
                continue
            # If the client is new, initialize the buffers and expected sequences
            if client_id not in self.expected_sequences:
                self.expected_sequences[client_id] = 0
                self.received_chunks[client_id] = {}
                self.buffers[client_id] = b''
            self.received_chunks[client_id][sequence_number] =  chunk_data

            while self.expected_sequences[client_id] in self.received_chunks[client_id]:
                self.buffers[client_id] += self.received_chunks[client_id].pop(self.expected_sequences[client_id])
                self.expected_sequences[client_id] += 1

            if len(self.buffers[client_id]) < data_len:
                continue
            # Decode the frame using ffmpeg
            process = (
                ffmpeg
                .input('pipe:0', format='h264')
                .output('pipe:1', format='rawvideo', pix_fmt='rgb24')
                .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
            )
            out, _ = process.communicate(input=self.buffers[client_id])
            # transform the byte string into a numpy array
            frame = np.frombuffer(out, np.uint8).reshape(camera_width, camera_height, 3)
            # Store the new frame in the dictionary
            self.frames[client_id] = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            camera_images = list(self.frames.values())
            grid_size = int(math.ceil(math.sqrt(len(camera_images))))
            # Overlay the camera images in a grid using the overlay_camera_images function in **util.py**
            grid_image = overlay_camera_images(camera_images, (grid_size, grid_size))
            cv2.imshow('Video Grid', grid_image)
            # Clear the buffer for next frame
            self.buffers[client_id] = b''
            self.expected_sequences[client_id] = 0
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def remove_client(self, client_id):
        self.buffers.pop(client_id, None)
        self.expected_sequences.pop(client_id, None)
        self.received_chunks.pop(client_id, None)
        self.frames.pop(client_id, None)
        if not self.buffers or not self.expected_sequences or not self.received_chunks or not self.frames:
            cv2.destroyAllWindows()

    def clear(self):
        self.buffers.clear()
        self.expected_sequences.clear()
        self.received_chunks.clear()
        self.frames.clear()

    def terminate(self):
        self._running = False
        cv2.destroyAllWindows()
        self.clear()
