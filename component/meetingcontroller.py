from enum import Enum
from typing import Union

from PIL.Image import Image
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QImage

from common.user import User
from view.meetingscreen import MeetingInterfaceBase

class MeetingType(Enum):
    OWNEDSINGLE = 0 # owned single user meeting
    NONOWNEDSINGLE = 1 # non-owned single user meeting
    OWNEDMULTIPUL = 2 # owned multiple user meeting
    NONOWNEDMULTIPUL = 3 # non-owned multiple user meeting

class MeetingController(QObject):

    closed = MeetingInterfaceBase.close_signal
    message_received = pyqtSignal(str, str) # sender_name, message
    video_received = pyqtSignal(bytes)
    audio_received = pyqtSignal(bytes)

    def __init__(self, meetingUI: MeetingInterfaceBase, app, user_view, meeting_type=MeetingType.OWNEDSINGLE):
        super().__init__()
        self.meetingUI = meetingUI
        self.app = app
        self.chatArea = self.meetingUI.chatArea
        self.displayArea = self.meetingUI.displayArea
        self.isOwned = meeting_type in (MeetingType.OWNEDSINGLE, MeetingType.OWNEDMULTIPUL)
        self.user_view = user_view # type: User
        self.meeting_type = meeting_type # type: MeetingType

        # connect signal
        self.meetingUI.close_signal.connect(self.closed)
        self.chatArea.sendButton.clicked.connect(self.handle_message_send)
        self.message_received.connect(self.handle_message)
        self.video_received.connect(self.handle_video)

    def handle_message_send(self):
        message = self.chatArea.textEdit.toPlainText()
        self.chatArea.textEdit.clear()
        self.message_received.emit(self.user_view.username, message)

    def handle_screen_send(self, ):
        self.app.send_video_start('screen')

    def handle_camera_send(self, ):
        self.app.send_video_start('camera')

    def handle_video_stop(self, ):
        self.app.send_video_stop()

    def handle_audio(self, user_id, audio: bytes):
        # TODO play audio
        # self.io_device.write(audio)
        # self.audio_output.start(self.io_device)
        pass

    def handle_message(self, sender_name, message):
        self.chatArea.addMessage(sender_name, message)

    def handle_video(self, image_bytes: bytes):
        image = QImage.fromData(image_bytes)
        self.meetingUI.displayArea.set_image(image)
