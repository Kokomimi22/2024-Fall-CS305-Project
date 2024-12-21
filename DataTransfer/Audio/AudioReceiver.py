import socket
import threading

import pyaudio
from config import *


class AudioReceiver:
    def __init__(self, socket_connection: socket.socket, stream_out: pyaudio.Stream):
        self.stream = stream_out
        self.client_socket = socket_connection
        self.client_socket.setblocking(False)
        self._running = False
        self._thread = None

    def _recv_audio(self):
        while self._running:
            try:
                data, _ = self.client_socket.recvfrom(CHUNK * 2)
                if not data:
                    break
            except BlockingIOError:
                continue
            except OSError:
                break
            self.stream.write(data)


    def start(self):
        if self._running:
            raise RuntimeError("VideoReceiver is already running")
        self._running = True
        self._thread = threading.Thread(target=self._recv_audio)
        self._thread.start()

    def switch_socket(self, socket_connection: socket.socket):
        self.client_socket = socket_connection

    def terminate(self):
        if not self._running:
            return None
        self._running = False
        self._thread.join()