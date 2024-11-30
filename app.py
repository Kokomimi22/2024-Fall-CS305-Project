import sys

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

from common.conf_client import ConferenceClient
from util import *
from view.gui import LoginWindow
from view.gui import Main
from view.gui import TestInterface
from view.homescreen import setHomeController
from view.meetingscreen import MeetingInterfaceBase

conf_client = None

class AppController:
    def __init__(self, mainui: Main, loginui: LoginWindow, meetingui: MeetingInterfaceBase):
        self.mainui = mainui
        self.loginui = loginui
        self.meetingui = meetingui
        self.logincontol = LoginController(self.loginui, self)
        self.testcontrol = TestController(testui=self.mainui.testInterface, app=self)
        self.homeController = HomeController(homeui=self.mainui.homeInterface, app=self)
        self.loginui.close_signal.connect(self.stop)
        self.mainui.close_signal.connect(self.stop)
        # initial other controller

    def switch_ui(self, to='main'):
        if to == 'main':
            self.mainui.show()
            self.loginui.hide()
            self.meetingui.hide()
        elif to == 'login':
            self.mainui.hide()
            self.meetingui.hide()
            self.loginui.show()
        elif to == 'meeting':
            self.meetingui.show()
            self.mainui.hide()
            self.loginui.hide()
        else:
            pass

    def start(self):
        self.logincontol.register_all_action()
        self.testcontrol.register_all_action()
        pass

    def stop(self):
        self.testcontrol.stop_thread()
        self.logincontol.stop_thread()
        self.homeController.stop_thread()
        streamin.stop_stream()
        streamin.close()
        streamout.stop_stream()
        streamout.close()
        audio.terminate()
        QApplication.quit()

class HomeController:

    def __init__(self, homeui, app):
        self.interface = homeui
        setHomeController(self)
        self.app = app

    def get_all_available_confs(self):
        pass

    def join_conference(self):
        pass

    def switch_to_meeting_screen(self):
        self.app.switch_ui('meeting')

    def stop_thread(self):
        pass


class LoginController:
    def __init__(self, loginui: LoginWindow, app: AppController):
        self.loginui = loginui
        self.app = app

    def register_all_action(self):
        """
        self.pushButton = 'login'
        self.pushButton_3 = 'register'
        self.lineEdit_3 = 'username'
        self.lineEdit_4 = 'password'
        self.checkBox = 'isRemember'
        """
        self.loginui.pushButton.clicked.connect(self.login)
        self.loginui.pushButton_3.clicked.connect(self.register)

    def login(self):
        username = self.loginui.lineEdit_3.text()
        password = self.loginui.lineEdit_4.text()
        if not username or not password:
            # show error message
            self.loginui.info('error', 'Error', 'Username or password is empty')
            return
        # isRemember = self.loginui.checkBox.isChecked()
        # send login request to server
        server_response = conf_client.login(username, password)
        if server_response:
            self.loginui.info('success', 'Success', 'Log in successfully')
            # switch to main view
            self.switch_to_main()
        else:
            self.loginui.info('error', 'Error', 'Username or password is incorrect')

    def register(self):
        username = self.loginui.lineEdit_3.text()
        password = self.loginui.lineEdit_4.text()
        if not username or not password:
            # show error message
            self.loginui.info('error', 'Error', 'Username or password is empty')
            return
        # send register request to server
        # login automatically if register success
        server_response = conf_client.register(username, password)
        if server_response:
            self.loginui.info('success', 'Success', 'Register successfully')
            conf_client.login(username, password)
            self.switch_to_main()
        else:
            self.loginui.info('error', 'Error', 'Failed to register')

    def switch_to_main(self):
        # switch to main view
        self.app.switch_ui('main')
        pass

    def stop_thread(self):
        pass


class Work(QThread):
    trigger = pyqtSignal(QImage)

    def __init__(self):
        super(Work, self).__init__()

    def run(self):
        while not self.isInterruptionRequested():
            screen = capture_screen()
            qimage = screen.toqimage()
            qimage = qimage.scaled(640, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.trigger.emit(qimage)
            #self.msleep(16)  # approximately 60fps

    def stop(self):
        self.requestInterruption()
        self.wait()


class VoiceWork(QThread):
    trigger = pyqtSignal(bytes)

    def __init__(self):
        super(VoiceWork, self).__init__()

    def run(self):
        while not self.isInterruptionRequested():
            voice_bytes = capture_voice()
            self.trigger.emit(voice_bytes)
            self.msleep(int(CHUNK / RATE * 1000))

    def stop(self):
        self.requestInterruption()
        self.wait()


class TestController:

    def __init__(self, testui: TestInterface, app: AppController):
        self.interface = testui
        self.is_preview = False
        self.is_voice = False
        self.preview_thread = Work()
        self.voice_thread = VoiceWork()
        self.preview_thread.trigger.connect(self.update_preview)
        self.voice_thread.trigger.connect(self.play_voice)
        self.app = app

    def register_all_action(self):
        self.interface.previewarea.previewstartbutton.toggled.connect(self.toggle_preview)
        self.interface.soundpreviewarea.previewarea.playButton.clicked.connect(self.toggle_voice)

    def toggle_preview(self):
        self.is_preview = not self.is_preview

        if not self.is_preview:
            self.preview_thread.stop()
            # self.interface.previewarea.setImage(default)

        if self.is_preview:
            self.preview_thread.start()

    def toggle_voice(self):
        self.is_voice = not self.is_voice
        if not self.is_voice:
            self.voice_thread.stop()
        if self.is_voice:
            self.voice_thread.start()

    def update_preview(self, qimage: QImage):
        self.interface.set_preview(qimage)
        print('finish update preview')

    def play_voice(self, voice: bytes) -> None:
        self.interface.set_voice(voice)
        print('finish update voice')

    def stop_thread(self):
        if self.preview_thread and self.preview_thread.isRunning():
            self.preview_thread.stop()
        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.stop()
        self.preview_thread = None


from PyQt5.QtCore import Qt, QLocale
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

if __name__ == '__main__':
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # Internationalization
    translator = FluentTranslator(QLocale())
    app.installTranslator(translator)

    mainui = Main()
    loginui = LoginWindow()
    meetingui = MeetingInterfaceBase()
    conf_client = ConferenceClient()
    controller = AppController(mainui=mainui, loginui=loginui, meetingui=meetingui)
    controller.start()

    sys.exit(app.exec_())
