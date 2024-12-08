import queue
import threading
import socket
import struct
import zlib
import cv2
import numpy as np
from config import *


class VideoReceiver:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.buffers = {}  # Dictionary to store buffers for each client
        self.expected_sequences = {}  # Dictionary to store expected sequences for each client
        self.received_chunks = {}  # Dictionary to store received chunks for each client
        self.frames = {}  # Dictionary to store the latest frame for each client
        self.data_queue = queue.Queue()

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
        while True:
            data, _ = self.sock.recvfrom(DATA_LINE_BUFFER << 3)
            self.data_queue.put(data)

    def process_data(self):
        while True:
            data = self.data_queue.get()
            client_id, data_len, sequence_number, chunk_data = self._unpack_data(data)
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
                decompressed_data = zlib.decompress(self.buffers[client_id])
                frame = cv2.imdecode(np.frombuffer(decompressed_data, np.uint8), cv2.IMREAD_COLOR)
                self.frames[client_id] = frame
                self.buffers[client_id] = b''  # Reset for next frame
                self.expected_sequences[client_id] = 0
            except zlib.error:
                print(f"Error decompressing data for client {client_id}")
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.sock.close()
        cv2.destroyAllWindows()

    def display_frames(self):
        while True:
            if self.frames:
                grid_frame = self._create_grid_frame()
                cv2.imshow("Video Grid", grid_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        cv2.destroyAllWindows()

    def _create_grid_frame(self):
        frames = list(self.frames.values())
        num_frames = len(frames)
        grid_size = int(np.ceil(np.sqrt(num_frames)))
        frame_height, frame_width = frames[0].shape[:2]
        grid_frame = np.zeros((frame_height * grid_size, frame_width * grid_size, 3), dtype=np.uint8)

        for idx, frame in enumerate(frames):
            row = idx // grid_size
            col = idx % grid_size
            grid_frame[row * frame_height:(row + 1) * frame_height, col * frame_width:(col + 1) * frame_width] = frame

        return grid_frame

    def start(self):
        receive_thread = threading.Thread(target=self.receive_data)
        process_thread = threading.Thread(target=self.process_data)
        display_thread = threading.Thread(target=self.display_frames)

        receive_thread.start()
        process_thread.start()
        display_thread.start()

        receive_thread.join()
        process_thread.join()
        display_thread.join()
