import threading
import socket

from VideoReceiver import VideoReceiver
from VideoSender import VideoSender
from Camera import Camera

def main():
    camera = Camera()
    socket_connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_connection.bind(('localhost', 10000))
    receiver = VideoReceiver(socket_connection)
    socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket1.connect(('localhost', 10000))
    sender1 = VideoSender(camera, socket1, 'client1')
    socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket2.connect(('localhost', 10000))
    sender2 = VideoSender(camera, socket2, 'client2')
    socket3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket3.connect(('localhost', 10000))
    sender3 = VideoSender(camera, socket3, 'client3')
    sender1_thread = threading.Thread(target=sender1.start)
    sender2_thread = threading.Thread(target=sender2.start)
    sender3_thread = threading.Thread(target=sender3.start)
    receiver_thread = threading.Thread(target=receiver.start)

    sender1_thread.start()
    sender2_thread.start()
    sender3_thread.start()
    receiver_thread.start()

    sender1_thread.join()
    sender2_thread.join()
    sender3_thread.join()
    receiver_thread.join()

    camera.stop()

if __name__ == "__main__":
    main()