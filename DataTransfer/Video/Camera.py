import threading
import time
from os import fspath

from util import capture_camera, release_camera, capture_screen

class Camera:
    def __init__(self, mode='camera', fps=30):
        self.frame = (False, None)
        self.lock = threading.Lock()
        self.running = True
        self.mode = mode
        self.fps = fps
        self.interval = 1.0 / self.fps
        self.thread = threading.Thread(target=self.update_frame)
        self.thread.start()

    def update_frame(self):
        while self.running:
            start_time = time.time()
            if self.mode == 'camera':
                ret, frame = capture_camera()
            elif self.mode == 'screen':
                ret, frame = capture_screen()
            else:
                ret, frame = False, None

            with self.lock:
                self.frame = (ret, frame)

            elapsed_time = time.time() - start_time
            sleep_time = max(0.0, self.interval - elapsed_time)
            time.sleep(sleep_time)

    def get_frame(self):
        """
        get the current frame and thread safe
        """
        with self.lock:
            return self.frame

    def switch_mode(self):
        """
        switch between camera and screen
        """
        if self.mode == 'camera':
           self.mode = 'screen'
           release_camera()
        else:
            self.mode = 'camera'

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()
            with self.lock:
                self.frame = (False, None)
            release_camera()