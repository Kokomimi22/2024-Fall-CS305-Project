from enum import Enum
from typing import Union

from PIL.Image import Image
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QImage
from qfluentwidgets import Action, FluentIcon

from common.user import User
from component.screencapture import CaptureMode, RegionCapture, WindowSelector, MaskedRegionSelector, FullScreenCapture, \
    Result, ScreenCapture
from config import MessageType
from view.meetingscreen import MeetingInterfaceBase

class MeetingController(QObject):

    closed = MeetingInterfaceBase.close_signal
    message_received = pyqtSignal(str, str) # sender_name, message
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
        self.isSpeaking = True
        self.isSharing = False
        # connect signal
        self.meetingUI.close_signal.connect(self.closed)
        self.commandBar.share_signal.connect(self.handle_video_send)
        self.commandBar.quit_signal.connect(self.handle_quit)
        self.commandBar.cancel_signal.connect(self.handle_cancel)
        self.commandBar.mode_changed.connect(self.handle_capture_mode)
        self.chatArea.sendButton.clicked.connect(self.handle_message_send)
        self.message_received.connect(self.handle_message)
        self.video_received.connect(self.handle_video)
        self.audio_control.triggered.connect(self.handle_audio_toggle)

        self.region_selector = MaskedRegionSelector()
        self.window_selector = WindowSelector(self.meetingUI)
        self.window_selector.close()

        self.region_selector.result_returned.connect(self.handle_screen_capture_config)
        self.window_selector.result_returned.connect(self.handle_screen_capture_config)

    def handle_message_send(self):
        try:
            message = self.chatArea.textEdit.toPlainText()
            self.chatArea.textEdit.clear()
            self.message_received.emit(self.user_view.username, message)
            self.app.send_text_message(message)
        except Exception as e:
            self.meetingUI.info('error', 'Error', 'Failed to send message')
            print(e)

    def handle_capture_mode(self, mode: int):
        if mode == CaptureMode.FULL_SCREEN.value:
            self.app.send_video_start('screen', FullScreenCapture())
            print('region', FullScreenCapture())
        elif mode == CaptureMode.REGION.value:
            self.region_selector = MaskedRegionSelector()
            self.region_selector.result_returned.connect(self.handle_screen_capture_config)
            self.region_selector.show()
        elif mode == CaptureMode.WINDOW.value:
            self.window_selector.show()

    def handle_screen_capture_config(self, config: Result):
        if config.mode == CaptureMode.WINDOW:
            self.app.send_video_start('screen', ScreenCapture.fromResult(config))
            print('window', config)
        elif config.mode == CaptureMode.FULL_SCREEN:
            self.app.send_video_start('screen', ScreenCapture.fromResult(config))
            print('full screen', config)
        elif config.mode == CaptureMode.REGION:
            self.app.send_video_start('screen', ScreenCapture.fromResult(config))
            print('region', config)
        else:
            print('Invalid capture mode')

    def handle_video_send(self, str):
        try:
            if str == 'stop':
                self.app.send_video_stop()
                self.isSharing = False
            else:
                if self.isSharing:
                    self.app.send_video_switch_mode()
                    return
                self.isSharing = True
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

    def handle_message(self, sender_name, message):
        self.chatArea.addMessage(sender_name, message)

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