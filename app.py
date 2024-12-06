import sys

from common.conf_client import ConferenceClient
from component.audiopreview import AudioPreview
from component.videopreview import VideoPreview
from view.gui import LoginWindow
from view.gui import Main
from view.gui import TestInterface

conf_client = None


class AppController:
    def __init__(self, mainui: Main, loginui: LoginWindow):
        self.mainui = mainui
        self.loginui = loginui
        self.logincontol = LoginController(loginui, self)
        self.testcontrol = TestController(testui=self.mainui.testInterface, app=self)
        self.loginui.close_signal.connect(self.stop)
        self.mainui.close_signal.connect(self.stop)
        # initial other controller

        # test
        self.switch_ui('main')

    def switch_ui(self, to='main'):
        if to == 'main':
            self.mainui.show()
            self.loginui.hide()
        elif to == 'login':
            self.mainui.hide()
            self.loginui.show()
        else:
            pass

    def start(self):
        self.logincontol.register_all_action()
        pass

    def stop(self):
        self.logincontol.stop_thread()
        QApplication.quit()

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

class TestController:

    def __init__(self, testui: TestInterface, app: AppController):
        self.interface = testui
        self.app = app
        self.video_preview = VideoPreview(self.interface.previewarea)
        self.audio_preview = AudioPreview(self.interface.soundpreviewarea)

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
    conf_client = ConferenceClient()
    controller = AppController(mainui, loginui=loginui)
    controller.start()

    sys.exit(app.exec_())
