import socket
import struct
import time
import pyaudio
from config import *

# Audio configuration
FORMAT = pyaudio.paInt16
RECEIVER_PORT = int(input())

class AudioSender:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = ('localhost', 5000)
        self.mute = False

    def start(self):
        print("Starting audio transmission...")
        try:
            while True:
                if self.mute:
                    data = b'\x00' * CHUNK * 2
                    self.server_socket.sendto(data, self.server_address)
                    print(f"Sent {len(data)} bytes")
                    time.sleep(1 / RATE * CHUNK)
                else:
                    data = self.stream.read(CHUNK)
                    self.server_socket.sendto(data, self.server_address)
                    print(f"Sent {len(data)} bytes")
        except KeyboardInterrupt:
            print("Transmission ended")
        finally:
            # 向服务器发送结束信号
            self.server_socket.sendto(b'END', self.server_address)
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            self.server_socket.close()




# Initialize pyaudio
audio = pyaudio.PyAudio()

# Create UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 5000)

# Send receiver port to server
server_socket.sendto(struct.pack('I', RECEIVER_PORT), server_address)

mute = False

stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

print("Starting audio transmission...")
try:
    while True:
        if mute:
            data = b'\x00' * CHUNK * 2
            server_socket.sendto(data, server_address)
            print(f"Sent {len(data)} bytes")
            time.sleep(1 / RATE * CHUNK)
        else:
            data = stream.read(CHUNK)
            server_socket.sendto(data, server_address)
            print(f"Sent {len(data)} bytes")
except KeyboardInterrupt:
    print("Transmission ended")
finally:
    # 向服务器发送结束信号
    server_socket.sendto(b'END', server_address)
    stream.stop_stream()
    stream.close()
    audio.terminate()
    server_socket.close()