import socket
import threading
import struct
import numpy as np
from config import *

# Audio configuration
FORMAT = np.int16

# Create UDP socket for receiving data from senders
receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receive_socket.bind(('localhost', 5000))

# Create UDP socket for sending data to receivers
send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Dictionary to store sender address and corresponding receiver port
sender_receiver_ports = {}
# Dictionary to store the latest audio buffer from each sender
audio_buffers = {}

def handle_client(data, address):
    if address not in sender_receiver_ports:
        receiver_port = struct.unpack('I', data[:4])[0]
        sender_receiver_ports[address] = receiver_port
        audio_buffers[address] = np.zeros(CHUNK, dtype=FORMAT)
        print(f"Registered sender {address} with receiver port {receiver_port}")
    elif data == b'END':
        del audio_buffers[address]
        print(f"Unregistered sender {address}")
    else:
        mixed_audio = mix_audio(data, address)
        client_address = ('localhost', sender_receiver_ports[address])
        send_socket.sendto(mixed_audio, client_address)
        audio_buffers[address] = np.zeros(CHUNK, dtype=FORMAT)

def mix_audio(data, address):
    if audio_buffers:
        for sender, buffer in audio_buffers.items():
            if sender == address:
                continue
            # 将data对齐形状
            data = data.ljust(CHUNK * 2, b'\x00')
            mixed_audio = np.add(buffer, np.frombuffer(data, dtype=FORMAT), casting="unsafe")
            mixed_audio = np.clip(mixed_audio, -32768, 32767)
            audio_buffers[sender] = mixed_audio
    return audio_buffers[address]

print("Server is running...")
try:
    while True:
        data, address = receive_socket.recvfrom(CHUNK * 2)
        threading.Thread(target=handle_client, args=(data, address)).start()
except KeyboardInterrupt:
    print("Server stopped")
finally:
    receive_socket.close()
    send_socket.close()