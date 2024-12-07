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
        self.buffer = b''
        self.expected_sequence = 0
        self.received_chunks = {}
        self.data_queue = queue.Queue()

    def receive_data(self):
        while True:
            data, _ = self.sock.recvfrom(DATA_LINE_BUFFER << 3)
            self.data_queue.put(data)

    def process_data(self):
        while True:
            # get方法会阻塞，直到队列中有数据，queue是线程安全的，不要担心多线程问题
            data = self.data_queue.get()
            Q_size = struct.calcsize("Q")
            I_size = struct.calcsize("I")
            data_len = struct.unpack("Q", data[:Q_size])[0]
            sequence_number = struct.unpack("I", data[Q_size:Q_size + I_size])[0]
            chunk_data = data[Q_size + I_size:Q_size + I_size + VIDEO_CHUNK_SIZE]

            self.received_chunks[sequence_number] = chunk_data

            while self.expected_sequence in self.received_chunks:
                self.buffer += self.received_chunks.pop(self.expected_sequence)
                self.expected_sequence += 1
            if len(self.buffer) < data_len:
                continue
            try:
                decompressed_data = zlib.decompress(self.buffer)
                frame = cv2.imdecode(np.frombuffer(decompressed_data, np.uint8), cv2.IMREAD_COLOR)
                cv2.imshow("Video", frame)
                self.buffer = b''  # Reset for next frame
                self.expected_sequence = 0
            except zlib.error:
                print("Error decompressing data")
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.sock.close()
        cv2.destroyAllWindows()

    def start(self):
        receive_thread = threading.Thread(target=self.receive_data)
        process_thread = threading.Thread(target=self.process_data)

        receive_thread.start()
        process_thread.start()

        receive_thread.join()
        process_thread.join()