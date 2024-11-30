# controller for video preview card widget

from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtProperty, pyqtSlot
from PyQt5.QtGui import QImage
from qfluentwidgets import FluentIcon

from view.testscreen import TestInterface

from math import ceil

from util import *

VideoPreviewCardView = TestInterface.VideoPreviewCard

class Work(QThread):
    trigger = pyqtSignal(QImage)

    def __init__(self, restInterval=16):
        super(Work, self).__init__()
        self.restInterval = restInterval # ms
        self.currentVideoSource = None

    def run(self):
        while not self.isInterruptionRequested():
            img = VideoPreviewCardView.DEFAULT_PREVIEW_HOLDER
            if not self.currentVideoSource:
                return
            elif isinstance(self.currentVideoSource, Desktop):
                img = capture_screen().toqimage()  # return QImage
            elif isinstance(self.currentVideoSource, QCameraInfo):
                img = qcapture_camera(QCamera(self.currentVideoSource))

            self.trigger.emit(img.copy())
            self.msleep(self.restInterval)

    def stop(self):
        self.requestInterruption()
        self.wait()

    def change_rest_interval(self, interval):
        self.restInterval = interval

    def setVideoSource(self, source):
        self.currentVideoSource = source

class VideoPreview:

    DEFAULT_PREVIEW_HOLDER = VideoPreviewCardView.DEFAULT_PREVIEW_HOLDER

    def __init__(self, view: VideoPreviewCardView):
        self.view = view
        self.is_preview = False
        self.preview_thread = Work()

        self.currentVideoSource = Desktop.default()
        self.availableVideoSources = {} # {sourceIndex: source}

        self.view.previewstartbutton.toggled.connect(self.handle_toggle)
        self.view.selecsrcButton.clicked.connect(self.update_aval_source)
        self.view.selecsrcButton.currentIndexChanged.connect(self.handle_source_change)
        self.preview_thread.trigger.connect(self.render_preview)

        self.view.previewstartbutton.setDisabled(True) # disable start preview button

    def handle_toggle(self):
        self.is_preview = not self.is_preview

        if not self.is_preview:
            self.preview_thread.stop()
            self.view.set_preview(self.DEFAULT_PREVIEW_HOLDER)

        if self.is_preview and self.currentVideoSource:
            self.preview_thread.start()

    def update_aval_source(self):
        avalVideos = getVideoDevices()
        avalVideos.append(Desktop.default())

        self.view.selecsrcButton.clear()

        for i, a in enumerate(avalVideos):
            if not isinstance(a, Desktop):
                icon = FluentIcon.CAMERA
            else:
                icon = FluentIcon.VIDEO
            self.view.selecsrcButton.addItem(a.deviceName, icon)
            self.availableVideoSources[i] = a

    def handle_source_change(self, index):
        self.currentVideoSource = self.availableVideoSources.get(index) or self.currentVideoSource
        if self.currentVideoSource:
            self.view.previewstartbutton.setDisabled(False)
            self.preview_thread.setVideoSource(self.currentVideoSource)

    def render_preview(self, image=DEFAULT_PREVIEW_HOLDER): # connect to trigger signal
        assert isinstance(image, QImage)
        if self.is_preview:
            self.view.set_preview(image)

    @staticmethod
    def framerate_to_interval_ms(fps):
        return ceil(1000 / fps)

# constansts
class Desktop:
    def __init__(self):
        self.deviceName = 'Desktop Screen'
        self.icon = FluentIcon.FULL_SCREEN

    @staticmethod
    def default():
        return Desktop()