import queue
import socket
import struct
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import ffmpeg
import numpy as np

from config import *
from util import overlay_camera_images


class VideoReceiver:
    def __init__(self, socket_connection: socket.socket, frame_rate=30):
        self.sock = socket_connection
        self.buffers = {}  # Dictionary to store buffers for each client
        self.expected_sequences = {}  # Dictionary to store expected sequences for each client
        self.received_chunks = {}  # Dictionary to store received chunks for each client

        """
        Dictionary to store priority queues for each client, the priority is the timestamp.
        This is used to display the frames in the correct order and smoothness.
        """
        self.frame_queues = {}

        self._running = False
        self.executor = ThreadPoolExecutor(max_workers=3)  # Create a thread pool with 3 workers
        self.frame_interval = 1.0 / frame_rate

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
        timestamp = struct.unpack_from("d", data, offset)[0]
        offset += struct.calcsize("d")
        chunk_data = data[offset:]
        return client_id, data_len, sequence_number, timestamp, chunk_data

    def process_data(self):
        while self._running:
            try:
                data, _ = self.sock.recvfrom(65535)
                if data == b'Cancelled':
                    break
            except ConnectionResetError:
                print("Connection reset by the server")
                break
            client_id, data_len, sequence_number, timestamp, chunk_data = self._unpack_data(data)
            if chunk_data == b'TERMINATE':
                self.remove_client(client_id)
                continue
            # If the client is new, initialize the buffers and expected sequences
            if client_id not in self.expected_sequences:
                self.expected_sequences[client_id] = 0
                self.received_chunks[client_id] = {}
                self.buffers[client_id] = b''
                self.frame_queues[client_id] = queue.PriorityQueue()
            self.received_chunks[client_id][sequence_number] = (timestamp, chunk_data)

            while self.expected_sequences[client_id] in self.received_chunks[client_id]:
                timestamp, chunk = self.received_chunks[client_id].pop(self.expected_sequences[client_id])
                self.buffers[client_id] += chunk
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
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            self.frame_queues[client_id].put((timestamp, frame))
            # Clear the buffer for next frame
            self.buffers[client_id] = b''
            self.expected_sequences[client_id] = 0

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def display_frames(self):
        while self._running:
            frames_to_display = []
            for client_id, frame_queue in self.frame_queues.items():
                # Display the frames in the correct order
                _, frame = frame_queue.get()
                frames_to_display.append(frame)
            if not frames_to_display:
                continue
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            cv2.imshow('Video Grid', overlay_camera_images(frames_to_display))

    def remove_client(self, client_id):
        self.buffers.pop(client_id, None)
        self.expected_sequences.pop(client_id, None)
        self.received_chunks.pop(client_id, None)
        self.frame_queues.pop(client_id, None)

    def clear(self):
        self.buffers.clear()
        self.expected_sequences.clear()
        self.received_chunks.clear()
        for frame_queue in self.frame_queues.values():
            frame_queue.queue.clear()
        self.frame_queues.clear()

    def terminate(self):
        self._running = False
        self.executor.shutdown(wait=True)  # Shutdown the thread pool
        cv2.destroyAllWindows()
        self.clear()

    def start(self):
        self._running = True
        self.executor.submit(self.process_data)
        self.executor.submit(self.display_frames)