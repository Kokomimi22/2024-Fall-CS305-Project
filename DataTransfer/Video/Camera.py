import threading
from util import capture_camera, release_camera


class Camera:
    def __init__(self):
        self.frame = (False, None)
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self.update_frame)
        self.thread.start()

    def update_frame(self):
        while self.running:
            ret, frame = capture_camera()
            with self.lock:
                self.frame = (ret, frame)
    def get_frame(self):
        with self.lock:
            return self.frame

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()
            with self.lock:
                self.frame = (False, None)
            release_camera()