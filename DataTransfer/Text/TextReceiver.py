import json
import socket
import threading

from PyQt5.QtCore import pyqtSignal

from DataTransfer.Text.Commu import ResponseFormat


class TextReceiver:
    def __init__(self, server_socket: socket.socket, update_signal: pyqtSignal(str, str)):
        self.server_socket = server_socket
        self.update_signal = update_signal
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            raise RuntimeError("TextReceiver is already running")
        self._running = True
        self._thread = threading.Thread(target=self._recv_text)
        self._thread.start()

    def _recv_text(self):
        while self._running:
            try:
                data = self.server_socket.recv(1024)
                if not data:
                    break
                sender_name, message = ResponseFormat.unpack(json.loads(data.decode()))
                self.update_signal.emit(sender_name, message)
            except OSError as e:
                print(f"Error receiving text: {e}")
                break
            except ValueError as e:
                print(f"Error decoding text: {e}") # for debugging

    def switch_socket(self, socket_connection: socket.socket):
        self.server_socket = socket_connection

    def terminate(self):
        if not self._running:
            return None
        self._running = False
        self._thread.join()
        self.server_socket.close()