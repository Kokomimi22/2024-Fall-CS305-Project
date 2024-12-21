import socket

from DataTransfer.Text.Commu import RequestFormat
from config import MessageType


class TextSender:
    def __init__(self, server_socket: socket.socket):
        self.server_socket = server_socket

    def send(self, sender_name: str, message: str):
        post = RequestFormat(MessageType.TEXT_MESSAGE.value, sender_name, message).pack()
        self.server_socket.send(post)

    def switch_socket(self, server_socket: socket.socket):
        self.server_socket = server_socket