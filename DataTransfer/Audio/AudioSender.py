import threading
import time
from config import *

class AudioSender:
    def __init__(self, socket_connection, client_id=None, stream_in=None):
        self.client_id = client_id.encode('utf-8') if client_id else b''
        self.stream = stream_in
        self.server_socket = socket_connection
        self.sending = False
        self._running = False
        self._thread = None

    def _send_data(self):
        while self._running:
            if self.sending:
                data = self.stream.read(CHUNK)
                self.server_socket.send(data)
            else:
                data = b'\x00' * CHUNK * 2
                self.server_socket.send(data)
                time.sleep(1 / RATE * CHUNK)

    def start(self):
        if self._running:
            raise RuntimeError("AudioSender is already running")
        self._running = True
        self._thread = threading.Thread(target=self._send_data)
        self._thread.start()

    def terminate(self):
        try:
            self.server_socket.send(b'END')
        except OSError:
            pass
        if not self._running:
            return None
        self._running = False
        self._thread.join()
