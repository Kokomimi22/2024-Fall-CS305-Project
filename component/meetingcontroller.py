from enum import Enum
from typing import Union
import time

from PIL.Image import Image
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QImage
from qfluentwidgets import Action, FluentIcon

from common.user import User
from config import MessageType
from view.meetingscreen import MeetingInterfaceBase

class MeetingController(QObject):

    closed = MeetingInterfaceBase.close_signal
    message_received = pyqtSignal(str, str, str) # sender_name, message, timestamp
    video_received = pyqtSignal(Image)
    control_received = pyqtSignal(MessageType, str) # message_type, message

    def __init__(self, meetingUI: MeetingInterfaceBase, app, user_view, isOwned: bool):
        super().__init__()
        self.meetingUI = meetingUI
        self.app = app
        self.chatArea = self.meetingUI.chatArea
        self.displayArea = self.meetingUI.displayArea
        self.commandBar = self.meetingUI.commandBar.getCommandBar()
        self.volume_control = self.commandBar.volume_action
        self.audio_control: Action = self.commandBar.getAction('Speak')
        self.isOwned = isOwned
        self.user_view = user_view # type: User
        self.isMuted = False
        self.isSpeaking = False
        self.video_mode = ''
        # connect signal
        self.meetingUI.close_signal.connect(self.closed)
        self.meetingUI.commandBar.getCommandBar().share_signal.connect(self.handle_video_send)
        self.meetingUI.commandBar.getCommandBar().quit_signal.connect(self.handle_quit)
        self.meetingUI.commandBar.getCommandBar().cancel_signal.connect(self.handle_cancel)
        self.chatArea.sendButton.clicked.connect(self.handle_message_send)
        self.message_received.connect(self.handle_message)
        self.video_received.connect(self.handle_video)
        self.audio_control.triggered.connect(self.handle_audio_toggle)


    def handle_message_send(self):
        try:
            message = self.chatArea.textEdit.toPlainText()
            self.chatArea.textEdit.clear()
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            self.message_received.emit(self.user_view.username, message, timestamp)
            self.app.send_text_message(message)
        except Exception as e:
            self.meetingUI.info('error', 'Error', 'Failed to send message')
            print(e)

    def handle_video_send(self, str):
        try:
            if str == 'stop':
                self.app.send_video_stop()
                self.video_mode = ''
            else:
                if len(self.video_mode) > 0:
                    if str != self.video_mode:
                        self.app.send_video_switch_mode()
                        self.video_mode = str
                        print("video switch", str)
                    return
                self.video_mode = str
                self.app.send_video_start(str)
                print("video send", str)
        except Exception as e:
            self.meetingUI.info('error', 'Error', 'Failed to send video')
            print(e)

    def handle_audio_toggle(self):
        if self.isSpeaking:
            # update icon
            # stop speaking
            self.app.send_audio_stop()
            self.commandBar.setSpeak(False)
            self.isSpeaking = False
        else:
            # start speaking
            self.app.send_audio_start()
            self.commandBar.setSpeak(True)
            self.isSpeaking = True

    def handle_message(self, sender_name, message, timestamp):
        self.chatArea.addMessage(sender_name, message, timestamp)

    def handle_video(self, image: Image):
        image = image.toqimage()
        self.displayArea.set_image(image)

    def handle_quit(self):
        self.app.send_video_stop()
        self.meetingUI.close()
        self.app.mainui.show()

    def handle_cancel(self):
        try:
            self.app.mainui.show()
            self.app.send_video_stop()
            self.app.cancel_conference()
        except Exception as e:
            print(e)