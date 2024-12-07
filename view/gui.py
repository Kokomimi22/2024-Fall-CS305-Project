from qfluentwidgets import FluentTranslator, SplashScreen, ImageLabel

from PyQt5.QtCore import QEventLoop, QTimer, pyqtSignal, QSize, Qt

from view.loginscreen import LoginWindow

from view.homescreen import HomeInterface
from view.testscreen import TestInterface
from view.clickednavigationavatarwidget import ClickedNavigationAvatarWidget

from util import *

from resources import rc


class LoginWindow(LoginWindow):
    close_signal = pyqtSignal()
    def __init__(self):
        super().__init__()

        # 1. 创建启动页面
        self.loop = None
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))

        # 2. 在创建其他子页面前先显示主界面
        self.show()

        # 3. 创建子界面
        self.createSubInterface()

        # 4. 隐藏启动页面
        self.splashScreen.finish()

    def createSubInterface(self):
        self.loop = QEventLoop()
        QTimer.singleShot(1000, self.loop.quit)
        self.loop.exec_()
    def closeEvent(self, event):
        self.close_signal.emit()
        if self.loop and self.loop.isRunning():
            self.loop.quit()
        event.accept()

# Main window
import sys

from PyQt5.QtCore import QUrl, QLocale
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout
from qfluentwidgets import (NavigationItemPosition, MessageBox, FluentWindow,
                            NavigationAvatarWidget, SubtitleLabel, setFont)
from qfluentwidgets import FluentIcon as FIF


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class Main(FluentWindow):

    close_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # create sub interface
        self.homeInterface = HomeInterface(self)
        self.testInterface = TestInterface(self)
        self.settingInterface = Widget('Setting Interface', self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')
        self.addSubInterface(self.testInterface, FIF.APPLICATION, 'Test')

        self.navigationInterface.addSeparator()

        # add custom widget to bottom
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=ClickedNavigationAvatarWidget('zhiyiYo', 'resources/shoko.png'),
            onClick=None,
            position=NavigationItemPosition.BOTTOM,
        )

        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)


        # NOTE: enable acrylic effect
        self.navigationInterface.setAcrylicEnabled(True)

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('PyQt-Fluent-Widgets')

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

        # set the minimum window width that allows the navigation panel to be expanded
        # self.navigationInterface.setMinimumExpandWidth(900)
        # self.navigationInterface.expand(useAni=False)
    def closeEvent(self, event):
        self.close_signal.emit()
        event.accept()

def show():
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    # Internationalization
    translator = FluentTranslator(QLocale())
    app.installTranslator(translator)

    w = Main()
    w.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    show()
