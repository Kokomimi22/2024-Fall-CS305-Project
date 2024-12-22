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
        self.sock_lock = threading.Lock()

    def _send_data(self):
        # 为了避免在发送数据时出现问题，先等待服务器或者P2P同伴准备好
        time.sleep(3.0)
        while self._running:
            if self.sending:
                data = self.stream.read(CHUNK)
                with self.sock_lock:
                    self.server_socket.send(data)
            else:
                data = b'\x00' * CHUNK * 2
                with self.sock_lock:
                    self.server_socket.send(data)
                time.sleep(1 / RATE * CHUNK)

    def start(self):
        if self._running:
            raise RuntimeError("AudioSender is already running")
        self._running = True
        self._thread = threading.Thread(target=self._send_data)
        self._thread.start()

    def reconnect(self, address):
        with self.sock_lock:
            self.server_socket.connect(address)

    def terminate(self):
        try:
            self.server_socket.send(b'END')
        except OSError:
            pass
        if not self._running:
            return None
        self._running = False
        self._thread.join()
