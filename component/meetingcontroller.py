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
    camera_received = pyqtSignal(str, bytes) # user_id, image
    screen_received = pyqtSignal(str, bytes) # user_id, image
    audio_received = pyqtSignal(str, bytes) # user_id, audio

    def __init__(self, meetingUI: MeetingInterfaceBase, app, user_view, meeting_type=MeetingType.OWNEDSINGLE):
        super().__init__()
        self.meetingUI = meetingUI
        self.app = app
        self.chatArea = self.meetingUI.chatArea
        self.displayArea = self.meetingUI.displayArea
        self.isOwned = meeting_type in (MeetingType.OWNEDSINGLE, MeetingType.OWNEDMULTIPUL)
        self.user_view = user_view # type: User
        self.meeting_type = meeting_type # type: MeetingType
        self.bound = (0, 0) # record (row, col) of the last user in display grid

        self.displayGrid = []
        self.pos_map = {} # {user_id: pos}

        # connect signal
        self.meetingUI.close_signal.connect(self.closed)
        self.chatArea.sendButton.clicked.connect(self.handle_message_send)
        self.message_received.connect(self.handle_message)

    def handle_message_send(self):
        message_html = self.chatArea.textEdit.toHtml() # TODO: extract text from html
        message = self.chatArea.textEdit.toPlainText()
        self.chatArea.textEdit.clear()
        self.message_received.emit(self.user_view.username, message)

    def handle_screen_send(self, image):
        # TODO send screen
        if self.meeting_type != MeetingType.NONOWNEDSINGLE:
            self.handle_screen(self.user_view.user_id, image)
        # conf_client.send_screen(image)
        pass

    def handle_camera_send(self, image):
        # TODO send camera
        if self.meeting_type != MeetingType.NONOWNEDSINGLE:
            self.handle_camera(self.user_view.user_id, image)
        # conf_client.send_camera(image)
        pass

    def handle_audio(self, user_id, audio: bytes):
        # TODO play audio
        # self.io_device.write(audio)
        # self.audio_output.start(self.io_device)
        pass

    def handle_message(self, sender_name, message):
        self.chatArea.addMessage(sender_name, message)

    def handle_screen(self, user_id, image: Union[bytes, Image]):
        if user_id not in self.pos_map:
            # TODO add user to display grid, update bound
            pass
        else:
            pos = self.pos_map[user_id]
            self.displayGrid[pos].setScreen(image)

    def handle_camera(self, user_id, image: Union[bytes, Image]):
        if user_id not in self.pos_map:
            # TODO add user to display grid, update bound
            pass
        else:
            pos = self.pos_map[user_id]
            self.displayGrid[pos].setCamera(image)
