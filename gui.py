from qfluentwidgets import FluentTranslator, SplashScreen

from PyQt5.QtCore import QEventLoop, QTimer, QSize, QLocale, pyqtSignal

from ui.loginscreen import LoginWindow
from uiconfig import *

from ui.Ui_LoginWindow import rc

from util import *

import sys

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

from PyQt5.QtCore import Qt, QUrl, QLocale
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont, InfoBadge,
                            InfoBadgePosition, FluentBackgroundTheme)
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

from qfluentwidgets import ElevatedCardWidget, IconWidget, BodyLabel, CaptionLabel, PrimaryPushButton, ImageLabel, FluentIcon, AvatarWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect, QGraphicsBlurEffect

class ConferenceCard(QFrame):

    LIVING_ICON_PATH = ':/images/living.gif'

    def __init__(self, title, avartar, id, parent=None):
        '''
        title: str
        avartar: list[IconWidget]
        id: str
        icon: str
        '''
        super().__init__(parent)

        self.id = id


        avartar = AvatarWidget(self)
        avartar.setText('Z')

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(10)

        # self.iconWidget = ImageLabel(DEFAULT_ICON_PATH, self)
        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(f'id:{id}', self)
        self.joinButton = QPushButton(icon=FluentIcon.ADD_TO.icon(color=QColor('#9c89d3')), parent=self)
        self.extraButton = None

        self.setObjectName('conference-card')
        self.setFixedHeight(160)
        self.setFixedWidth(350)

        # set title
        titleFont = QFont()
        titleFont.setBold(True)
        titleFont.setPointSize(16)
        titleFont.setFamilies(['Trebuchet MS', 'Microsoft YaHei'])
        self.titleLabel.setFont(titleFont)
        self.titleLabel.setStyleSheet('color: white;')
        self.titleLabel.setAlignment(Qt.AlignLeft)
        self.titleLabel.setWordWrap(True)

        # set content
        contentFont = QFont()
        contentFont.setPointSize(10)
        contentFont.setFamily('Arial') # for id text
        self.contentLabel.setFont(contentFont)
        self.contentLabel.setStyleSheet('color: #e6e6e6;')
        self.contentLabel.setAlignment(Qt.AlignLeft)
        self.contentLabel.setWordWrap(True)

        # bottom layout
        self.bottomLayout = QHBoxLayout()

        # avatar area (overlapp style)
        avatars_layout = QHBoxLayout()
        avatars_layout.setContentsMargins(0, 0, 0, 0)
        avatars_layout.maximumSize = QSize(100, 40)
        creatorFont = QFont()
        creatorFont.setPointSize(13)
        creatorFont.setFamily('Microsoft YaHei')
        self.creatorLabel = QLabel('创建者', self)
        self.creatorLabel.setStyleSheet('color: white;')
        self.creatorLabel.setAlignment(Qt.AlignCenter)
        self.creatorLabel.setFont(creatorFont)
        avatars_layout.setSpacing(10)
        avartar.setRadius(20)
        # avatar.setStyleSheet("border-radius: 20px; border: 2px solid white;")
        avartar.setAlignment(Qt.AlignCenter)
        avartar.setStyleSheet("""
            border-radius: 20px;
            border: 1px solid white;
            """)
        self.livingLabel = ImageLabel(self.LIVING_ICON_PATH, self)
        
        avatars_layout.addWidget(self.creatorLabel, 0, Qt.AlignCenter)
        avatars_layout.addWidget(avartar, 0, Qt.AlignCenter)  
        avatars_layout.addWidget(self.livingLabel, 0, Qt.AlignCenter) 

        self.bottomLayout.addLayout(avatars_layout)
        self.bottomLayout.addStretch()

        # button area
        self.buttonLayout = QHBoxLayout()
        self.joinButton.setText('加入')
        self.joinButton.setFixedHeight(35)
        self.joinButton.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #9c89d3;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
                padding-left: 20px;
                padding-right: 20px
            }
            QPushButton:hover {
                background-color: #ecebff;

            }
            QPushButton:pressed {
                background-color: #dcd0ff;
            }
            QIcon {
                padding-right: 10px;
            }
            QIcon:hover {
                color: #9cffd3;
            }
        """)
        if self.extraButton:
            self.buttonLayout.addWidget(self.extraButton, 0, Qt.AlignRight) # extra button for more actions
        self.buttonLayout.addWidget(self.joinButton, 0, Qt.AlignRight)
        self.bottomLayout.addLayout(self.buttonLayout)

        # add widgets to main layout
        self.mainLayout.addWidget(self.titleLabel)
        self.mainLayout.addWidget(self.contentLabel)
        self.mainLayout.addStretch()
        self.mainLayout.addLayout(self.bottomLayout)

        # set style (gradient blue and blue purple background)
        self.setStyleSheet("""
            #conference-card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4e9df3, stop:1 #7cd9fb);
                border-radius: 10px;
            }
            #conference-card:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6eb8f3, stop:1 #9ce6fb);
            }
        """)
        dropShadowEffect = QGraphicsDropShadowEffect()
        dropShadowEffect.setBlurRadius(20)
        dropShadowEffect.setColor(QColor(0, 0, 0, 100))
        dropShadowEffect.setOffset(0, 0)
        self.setGraphicsEffect(dropShadowEffect)

        self.joinButton.setText('加入')

    def top_view(self):
        parent = self.parent()
        while parent:
            parent = parent.parent()
            if parent.objectName() == 'Home-Interface':
                break
        return parent


    def showMessageBox(self):
        w = MessageBox(
            '加入会议',
            '您确定要加入这个会议吗？',
            self.top_view()
        )
        w.yesButton.setText('加入')
        w.cancelButton.setText('取消')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://www.google.com"))

from qfluentwidgets import SingleDirectionScrollArea, TogglePushButton

class TestInterface(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('Test-Interface')
        self.vbox = QVBoxLayout(self)
        self.vbox.setContentsMargins(10, 10, 10, 10)
        self.vbox.setSpacing(0)
        self.subhbox = QHBoxLayout()

        # initial screen preview
        self.previewarea = ImageLabel(self)
        self.previewarea.setBorderRadius(8, 8, 8, 8)
        self.previewarea.setMaximumWidth(500)

        self.previewstartbutton = TogglePushButton("start preview")

        self.subhbox.addWidget(self.previewarea, alignment=Qt.AlignCenter)
        self.subhbox.addWidget(self.previewstartbutton, alignment=Qt.AlignCenter)
        self.vbox.addLayout(self.subhbox)

    def set_preview(self, img):
        self.previewarea.setImage(img)
        self.previewarea.setMaximumHeight(360)

from qfluentwidgets import PrimaryToolButton
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window

class HomeInterface(QFrame):

    CREATE_ICON_PATH = ':/images/create.png'
    ONLINE_ICON_PATH = ':/images/online.png'

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName('Home-Interface')
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(10)

        # create a subtitle label "Start your first meeting/开始你的第一个会议"
        self.firstLabel = SubtitleLabel('开始你的第一个会议', self)
        self.firstLabel.setAlignment(Qt.AlignCenter)
        self.mainLayout.addWidget(self.firstLabel, alignment=Qt.AlignLeft, stretch=5)

        # spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # self.mainLayout.addItem(spacerItem)

        # create a labelbutton "Create Meeting/创建会议" in the center 50 * 50
        self.createButton = PrimaryToolButton(self.CREATE_ICON_PATH, self)
        self.mainLayout.addWidget(self.createButton, alignment=Qt.AlignCenter, stretch=11)

        # create a subtitle label "on-going meetings/正在进行的会议 " in the center
        self.midBox = QHBoxLayout()
        self.onlineIcon = ImageLabel(self.ONLINE_ICON_PATH, self)
        self.onlineIcon.setFixedSize(30, 30)
        self.secondLabel = SubtitleLabel('正在进行的会议', self)
        self.secondLabel.setAlignment(Qt.AlignCenter)
        self.midBox.addWidget(self.onlineIcon, alignment=Qt.AlignLeft, stretch=0)
        self.midBox.addWidget(self.secondLabel, alignment=Qt.AlignLeft, stretch=12)

        self.mainLayout.addLayout(self.midBox)
        # self.mainLayout.addStretch()

        # create a scroll area for conference cards
        view = QWidget(self)
        view.setObjectName('conference-view')
        view.setStyleSheet("""
            #conference-view {
                background: #f9f9f9;
            }
        """)
        layout = QHBoxLayout(view)
        self.scrollArea = SingleDirectionScrollArea(self, orient=Qt.Horizontal)
        self.scrollArea.setFixedHeight(200)
        self.scrollArea.setObjectName('conference-scroll-area')
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        # create 5 conference cards for testing
        for i in range(5):
            card = ConferenceCard(f'Conference {i}', [], uuid.uuid4(), self)
            card.joinButton.clicked.connect(card.showMessageBox)
            layout.addWidget(card)

        self.scrollArea.setWidget(view)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.mainLayout.addWidget(self.scrollArea)



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
            widget=NavigationAvatarWidget('zhiyiYo', 'resources/shoko.png'),
            # onClick=self.showMessageBox,
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

    w = LoginWindow()
    w.show()
    app.exec_()
    sys.exit(app.exec_())
if __name__ == '__main__':
    show()
