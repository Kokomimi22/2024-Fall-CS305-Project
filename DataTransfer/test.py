import threading

from DataTransfer.VideoReceiver import VideoReceiver
from DataTransfer.VideoSender import VideoSender


def main():
    receiver = VideoReceiver('localhost', 10000)
    sender = VideoSender('localhost', 9999, ('localhost', 10000))

    sender_thread = threading.Thread(target=sender.start)
    receiver_thread = threading.Thread(target=receiver.start)

    sender_thread.start()
    receiver_thread.start()

    sender_thread.join()
    receiver_thread.join()

if __name__ == "__main__":
    main()