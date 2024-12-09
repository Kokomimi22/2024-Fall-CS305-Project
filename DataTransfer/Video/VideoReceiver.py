import queue
import socket
import struct
import threading
import zlib
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

from util import decompress_image, overlay_camera_images


class VideoReceiver:
    def __init__(self, socket_connection: socket.socket):
        self.sock = socket_connection
        self.buffers = {}  # Dictionary to store buffers for each client
        self.expected_sequences = {}  # Dictionary to store expected sequences for each client
        self.received_chunks = {}  # Dictionary to store received chunks for each client
        self.frames = {}  # Dictionary to store the latest frame for each client
        self.data_queue = queue.Queue()
        self._running = False
        self.executor = ThreadPoolExecutor(max_workers=3)  # Create a thread pool with 3 workers

    @staticmethod
    def _unpack_data(data):
        client_id_len = struct.unpack("I", data[:4])[0]
        client_id = data[4:4 + client_id_len].decode('utf-8')
        Q_size = struct.calcsize("Q")
        I_size = struct.calcsize("I")
        data_len = struct.unpack("Q", data[4 + client_id_len:4 + client_id_len + Q_size])[0]
        sequence_number = struct.unpack("I", data[4 + client_id_len + Q_size:4 + client_id_len + Q_size + I_size])[0]
        chunk_data = data[4 + client_id_len + Q_size + I_size:]
        return client_id, data_len, sequence_number, chunk_data

    def receive_data(self):
        while self._running:
            try:
                data, _ = self.sock.recvfrom(65535)
                if data == b'Cancelled':
                    break
                self.data_queue.put(data)
            except ConnectionResetError:
                print("Connection reset by peer")
                break

    def process_data(self):
        while self._running:
            data = self.data_queue.get()
            client_id, data_len, sequence_number, chunk_data = self._unpack_data(data)
            if chunk_data == b'TERMINATE':
                self.remove_client(client_id)
                continue
            if client_id not in self.expected_sequences:
                self.expected_sequences[client_id] = 0
                self.received_chunks[client_id] = {}
                self.buffers[client_id] = b''
            self.received_chunks[client_id][sequence_number] = chunk_data

            while self.expected_sequences[client_id] in self.received_chunks[client_id]:
                self.buffers[client_id] += self.received_chunks[client_id].pop(self.expected_sequences[client_id])
                self.expected_sequences[client_id] += 1

            if len(self.buffers[client_id]) < data_len:
                continue
            try:
                frame = decompress_image(self.buffers[client_id])
                self.frames[client_id] = frame
                self.buffers[client_id] = b''  # Reset for next frame
                self.expected_sequences[client_id] = 0
            except zlib.error:
                print(f"Error decompressing data for client {client_id}")
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def display_frames(self):
        while self._running:
            if self.frames:
                screen_image = None  # TODO: Replace with actual screen image if available
                camera_images = list(self.frames.values())
                if not camera_images:
                    continue
                grid_frame = overlay_camera_images(screen_image, camera_images)
                grid_frame_cv = np.array(grid_frame)  # Convert PIL.Image to numpy array for OpenCV
                cv2.imshow("Video Grid", grid_frame_cv)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    def remove_client(self, client_id):
        self.frames.pop(client_id, None)
        self.buffers.pop(client_id, None)
        self.expected_sequences.pop(client_id, None)
        self.received_chunks.pop(client_id, None)

    def clear(self):
        self.buffers.clear()
        self.expected_sequences.clear()
        self.received_chunks.clear()
        self.frames.clear()

    def terminate(self):
        self._running = False
        self.executor.shutdown(wait=True)  # Shutdown the thread pool
        cv2.destroyAllWindows()
        self.clear()

    def start(self):
        self._running = True
        self.executor.submit(self.receive_data)
        self.executor.submit(self.process_data)
        self.executor.submit(self.display_frames)
