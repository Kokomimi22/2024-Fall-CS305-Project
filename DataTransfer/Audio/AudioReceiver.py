import socket
import pyaudio
from config import *

# Audio configuration
FORMAT = pyaudio.paInt16

class AudioReceiver:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind(('localhost', 0))  # Bind to an available port
        self.receiver_port = self.client_socket.getsockname()[1]  # Get the assigned port

    def start(self):
        print(f"Starting audio reception on port {self.receiver_port}...")
        try:
            while True:
                data, _ = self.client_socket.recvfrom(CHUNK * 2)
                print(f"Received {len(data)} bytes: {data}")
                if not data:
                    break
                self.stream.write(data)
        except KeyboardInterrupt:
            print("Reception ended")
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            self.client_socket.close()