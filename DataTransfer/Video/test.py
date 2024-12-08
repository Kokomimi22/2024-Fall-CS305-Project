import threading
from VideoReceiver import VideoReceiver
from VideoSender import VideoSender
from Camera import Camera

def main():
    camera = Camera()
    receiver = VideoReceiver('localhost', 10000)
    sender1 = VideoSender(camera, ('localhost', 10000), 'client1')
    sender2 = VideoSender(camera, ('localhost', 10000), 'client2')
    sender3 = VideoSender(camera, ('localhost', 10000), 'client3')
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