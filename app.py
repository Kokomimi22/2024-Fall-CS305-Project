
from gui import Main
from gui import LoginWindow
from gui import TestInterface

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QImage, QPixmap

from util import *

import sys

from conf_client import *

class AppController:
    def __init__(self, mainui: Main, loginui: LoginWindow):
        self.mainui = mainui;
        self.loginui = loginui;
        self.logincontol = LoginController(loginui, self)
        self.testcontrol = TestController(testui=self.mainui.testInterface, app=self)
        # initial other controller

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
        self.testcontrol.register_all_action()
        pass


class LoginController:
    def __init__(self, loginui: LoginWindow, app: AppController):
        self.loginui = loginui
        self.app = app

    def register_all_action(self):
        '''
        self.pushButton = 'login'
        self.pushButton_3 = 'register'
        self.lineEdit_3 = 'username'
        self.lineEdit_4 = 'password'
        self.checkBox = 'isRemember'
        '''
        self.loginui.pushButton.clicked.connect(self.login)
        self.loginui.pushButton_3.clicked.connect(self.register)

    def login(self):
        username = self.loginui.lineEdit_3.text()
        password = self.loginui.lineEdit_4.text()
        if not username or not password:
            # show error message
            self.loginui.info('error', 'Error', 'Username or password is empty')
            return
        isRemember = self.loginui.checkBox.isChecked()
        # send login request to server
        pass
        # switch to main ui
        self.switch_to_main()

    def register(self):
        username = self.loginui.lineEdit_3.text()
        password = self.loginui.lineEdit_4.text()
        if not username or not password:
            # show error message
            return
        # send register request to server
        pass
        # login automatically if register success
        pass

    def switch_to_main(self):
        # switch to main ui
        self.app.switch_ui('main')
        pass

class Work(QThread):
        trigger = pyqtSignal(QImage)

        def __init__(self):
            super(Work, self).__init__()
        
        def run(self):
            while True:
                screen = capture_screen()
                qimage = screen.toqimage()
                qimage = qimage.scaled(640, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.trigger.emit(qimage)
                time.sleep(1/60) # 60fps
        

class TestController:

    def __init__(self, testui: TestInterface, app: AppController):
        self.interface = testui
        self.is_preview = False
        self.preview_thread = Work()
        self.preview_thread.trigger.connect(self.update_preview)
        self.app = app

    def register_all_action(self):
        self.interface.previewstartbutton.toggled.connect(self.toggle_preview)

    def toggle_preview(self):
        self.is_preview = not self.is_preview

        if not self.is_preview:
            self.preview_thread.terminate()
            # self.interface.previewarea.setImage(default)

        if self.is_preview:
            self.preview_thread.start()


    def update_preview(self, qimage: QImage):
        self.interface.set_preview(qimage)
        print('finish update preview')

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
    controller = AppController(mainui, loginui=loginui)
    controller.start()

    controller.switch_ui('main') # for test

    app.exec_()

    
    sys.exit(app.exec_())
