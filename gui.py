from qfluentwidgets import FluentTranslator, SplashScreen

from PyQt5.QtCore import QEventLoop, QTimer, QSize, QLocale

from ui.loginscreen import LoginWindow
from uiconfig import *

from ui.Ui_LoginWindow import rc

from util import *

import sys

class LoginWindow(LoginWindow):

    def __init__(self):
        super().__init__()
        
        # 1. 创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))

        # 2. 在创建其他子页面前先显示主界面
        self.show()

        self.createSubInterface()
        # 3. 创建子界面
        

        # 4. 隐藏启动页面
        self.splashScreen.finish()

    def createSubInterface(self):
        loop = QEventLoop()
        QTimer.singleShot(1000, loop.quit)
        loop.exec_()

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
        creatorFont.setFamily('Arial')
        creatorFont.setBold(True)
        self.creatorLabel = QLabel('Creator', self)
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

        self.joinButton.setText('Join')

    def top_view(self):
        parent = self.parent()
        while parent:
            parent = parent.parent()
            if parent.objectName() == 'Home-Interface':
                break
        return parent


    def showMessageBox(self):
        w = MessageBox(
            'Join meeting',
            'Do you want to join this meeting?',
            self.top_view()
        )
        w.yesButton.setText('Join')
        w.cancelButton.setText('Cancel')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://www.google.com"))

from qfluentwidgets import SingleDirectionScrollArea, TogglePushButton, HeaderCardWidget, FluentIcon, TitleLabel, ComboBox, SmoothScrollArea, ProgressBar, CardWidget
from qfluentwidgets.multimedia import SimpleMediaPlayBar, MediaPlayer
from qfluentwidgets.multimedia.media_play_bar import PlayButton, VolumeButton, MediaPlayBarBase, FluentStyleSheet
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget
from PyQt5.QtCore import QPropertyAnimation

class TestInterface(SmoothScrollArea):

    class VideoPreviewCard(HeaderCardWidget):

        DEFAULT_PREVIEW_HOLDER = QImage(640, 360, QImage.Format_RGB32)

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName('Video-Preview-Card')
            self.setTitle('Video Preview')
            self.mainLayout = QVBoxLayout()
            self.mainLayout.setSpacing(10)

            self.topLayout = QHBoxLayout()

            # initial screen preview
            self.previewarea = ImageLabel(self)
            self.previewarea.setBorderRadius(8, 8, 8, 8)
            self.previewarea.setImage(self.DEFAULT_PREVIEW_HOLDER)
            # self.previewarea.setMaximumWidth(500)

            self.topLayout.addWidget(self.previewarea)
            self.topLayout.addSpacerItem(QSpacerItem(50, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

            self.bottomLayout = QHBoxLayout()
            self.hintLabel = BodyLabel('Current video input:', self)
            self.hintLabel.setStyleSheet('color: #41b6bf;')
            self.bottomLayout.addWidget(self.hintLabel)
            self.selecsrcButton = ComboBox(self)
            self.selecsrcButton.setPlaceholderText('Select Source from')

            self.bottomLayout.addWidget(self.selecsrcButton)
            self.bottomLayout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

            self.previewstartbutton = TogglePushButton(FluentIcon.PLAY, "start preview")
            self.previewstartbutton.toggled.connect(self.handle_toggle)

            self.bottomLayout.addWidget(self.previewstartbutton)
            self.bottomLayout.addSpacerItem(QSpacerItem(220, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

            self.mainLayout.addLayout(self.topLayout)
            self.mainLayout.addLayout(self.bottomLayout)
            self.viewLayout.addLayout(self.mainLayout)


        def handle_toggle(self, checked):
            if checked:
                self.previewstartbutton.setIcon(FluentIcon.PAUSE)
                self.previewstartbutton.setText('stop preview')
            else:
                self.previewstartbutton.setIcon(FluentIcon.PLAY)
                self.previewstartbutton.setText('start preview')

    class SoundPreviewCard(HeaderCardWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName('Sound-Test-Card')
            self.setTitle('Sound Test')
            self.mainLayout = QVBoxLayout()
            self.mainLayout.setSpacing(20)

            self.topLayout = QHBoxLayout()

            # initial sound preview
            self.previewarea = self.SoundVisualizer(self)
            self.previewarea.setFixedHeight(48)
            self.mainLayout.addWidget(self.previewarea)
    

            self.hintLabel = BodyLabel('Current audio input:', self)
            self.hintLabel.setStyleSheet('color: #41b6bf;')
            self.topLayout.addWidget(self.hintLabel)
            self.selecsrcButton = ComboBox(self)
            self.selecsrcButton.setPlaceholderText('Select Source from')

            self.topLayout.addWidget(self.selecsrcButton)
            self.topLayout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

            self.topLayout.addSpacerItem(QSpacerItem(220, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

            self.mainLayout.addLayout(self.topLayout)
            self.viewLayout.addLayout(self.mainLayout)

        # def handle_toggle(self, checked):
        #     if checked:
        #         self.previewstartbutton.setIcon(FluentIcon.PAUSE)
        #         self.previewstartbutton.setText('stop')
        #     else:
        #         self.previewstartbutton.setIcon(FluentIcon.PLAY)
        #         self.previewstartbutton.setText('play')

        class SoundVisualizer(CardWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.player = None  # type: MediaPlayerBase

                self.playButton = PlayButton(self)
                self.volumeButton = VolumeButton(self)
                self.volumeButton.volumeView.volumeLabel.hide()
                self.progressSlider = ProgressBar(self)
                self.progressSlider.setRange(0, 100)
                self.progressSlider.setMaximumWidth(400)

                FluentStyleSheet.MEDIA_PLAYER.apply(self)

                self.hBoxLayout = QHBoxLayout(self)

                self.hBoxLayout.setContentsMargins(10, 4, 10, 4)
                self.hBoxLayout.setSpacing(6)
                self.hBoxLayout.addWidget(self.playButton, 0, Qt.AlignLeft)
                self.hBoxLayout.addWidget(self.progressSlider, 1)
                self.hBoxLayout.addWidget(self.volumeButton, 0)

                self.setFixedHeight(48)
                self.setFixedWidth(500)
                # self.setMediaPlayer(MediaPlayer(self))
                
            

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('Test-Interface')
        self.setStyleSheet("""
            #Test-Interface {
                background: transparent;
                }
        """)

        self.body = QWidget(self)
        self.body.setObjectName('Test-Interface-Body')
        self.body.setStyleSheet("""
            #Test-Interface-Body {
                background: transparent;
                }
        """)

        self.vbox = QVBoxLayout(self.body)
        self.vbox.setContentsMargins(20, 10, 20, 10)
        self.vbox.setSpacing(0)

        self.title = TitleLabel('Test your equipment', self)
        self.title.setAlignment(Qt.AlignCenter)
        self.vbox.addWidget(self.title, alignment=Qt.AlignLeft)
        self.subtitle = CaptionLabel('Check your camera and microphone', self)
        self.subtitle.setStyleSheet('color: gray;')
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.vbox.addWidget(self.subtitle, alignment=Qt.AlignLeft)

        self.vbox.addSpacerItem(QSpacerItem(20, 50, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.previewarea = self.VideoPreviewCard(self)
        self.vbox.addWidget(self.previewarea)

        self.vbox.addSpacerItem(QSpacerItem(20, 50, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.soundpreviewarea = self.SoundPreviewCard(self)
        self.vbox.addWidget(self.soundpreviewarea)
        
        self.setWidget(self.body)

    def set_preview(self, img):
        '''
        :param img: QImage
        '''
        if isinstance(img, QImage):
            img = img.scaled(640, 360)
        self.previewarea.previewarea.setImage(img)

from qfluentwidgets import PrimaryToolButton, SearchLineEdit, RoundMenu, Action
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPainter, QPainterPath, QLinearGradient, QBrush, QMovie
from PyQt5.QtCore import QRectF, Qt, QSize

class BannerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('Banner-Widget')
        self.setFixedHeight(346)

        self.mainLayout = QVBoxLayout(self)
        self.title = TitleLabel('Online meeting room', self)
        self.starterLabel = SubtitleLabel('Start your first meeting', self)
        self.banner = QImage(':/images/header.png')


        self.createButton = CreateButton(self)

        self.mainLayout.setContentsMargins(20, 0, 20, 0)
        self.mainLayout.setSpacing(10)

        self.title.setAlignment(Qt.AlignCenter)
        self.mainLayout.addWidget(self.title, alignment=Qt.AlignLeft)

        self.mainLayout.addSpacerItem(QSpacerItem(20, 110, QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))

        self.mainLayout.addWidget(self.starterLabel, alignment=Qt.AlignLeft)
        self.mainLayout.addWidget(self.createButton, alignment=Qt.AlignCenter)
        self.mainLayout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        painter.setPen(Qt.NoPen)

        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        w, h = self.width(), 241
        path.addRoundedRect(QRectF(0, 0, w, h), 10, 10)
        path.addRect(QRectF(0, h-50, 50, 50))
        path.addRect(QRectF(w-50, 0, 50, 50))
        path.addRect(QRectF(w-50, h-50, 50, 50))
        path = path.simplified()
        print(self.size())

        gradient = QLinearGradient(0, 0, 0, self.height())
        # draw background color

        gradient.setColorAt(0, QColor(207, 216, 228, 255))
        gradient.setColorAt(1, QColor(207, 216, 228, 0))
        # painter.fillPath(path, QBrush(gradient))

        qimage = self.banner.scaled(
           QSize(w, h), transformMode=Qt.SmoothTransformation)

        painter.fillPath(path, QBrush(qimage))

class CreateButton(QPushButton):


    CREATE_ICON_PATH = ':/images/create.png'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('Create-Button')
        self.setFixedSize(74, 74)
        self.setStyleSheet("""
            QPushButton#Create-Button {
                background-color: #ff9c1a;
                color: white;
                border-radius: 25px;
                }
            QPushButton#Create-Button:hover {
                background-color: #f1a644
                }
            QPushButton#Create-Button:pressed {
                background-color: #c7c4bf
                }
        """)
        self.setIcon(QIcon(self.CREATE_ICON_PATH))
        self.setIconSize(QSize(55, 55))
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)



class HomeInterface(QFrame):

    ONLINE_ICON_PATH = ':/images/online.png'

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName('Home-Interface')
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(20, 0, 20, 0)
        self.mainLayout.setSpacing(10)

        # create a banner widget
        self.banner = BannerWidget(self)
        self.body.addWidget(self.banner)

        # create a subtitle label "on-going meetings/正在进行的会议 " in the center
        self.midBox = QHBoxLayout()
        self.onlineIcon = ImageLabel(self.ONLINE_ICON_PATH, self)
        self.onlineIcon.setFixedSize(30, 30)
        self.secondLabel = SubtitleLabel('On-going meetings', self)
        self.secondLabel.setAlignment(Qt.AlignCenter)
        self.midBox.setContentsMargins(10, 0, 10, 0)
        self.midBox.addWidget(self.onlineIcon, alignment=Qt.AlignCenter, stretch=0)
        self.midBox.addWidget(self.secondLabel, alignment=Qt.AlignCenter, stretch=1)

        self.searchedit = SearchLineEdit(self)
        self.searchedit.setPlaceholderText('Search meetings...')
        self.searchedit.setFixedWidth(200)
        self.midBox.addWidget(self.searchedit, alignment=Qt.AlignCenter, stretch=2)
        self.midBox.addSpacerItem(QSpacerItem(350, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.mainLayout.addLayout(self.midBox)
        self.body.addLayout(self.mainLayout)
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

class NavigationAvatarWidget(NavigationAvatarWidget):
    '''
    override the click event
    '''
    def __init__(self, name: str, avatarPath: str, parent=None):
        super().__init__(name, avatarPath, parent)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if e.button() == Qt.LeftButton:
            self.createProfileWidget(e)
            

    class ProfileCard(QWidget):

        def __init__(self, avatarPath: str, name: str, email: str, parent=None):
            super().__init__(parent=parent)
            self.avatar = AvatarWidget(avatarPath, self)
            self.nameLabel = BodyLabel(name, self)
            self.emailLabel = CaptionLabel(email, self)

            self.setFixedSize(307, 82)
            self.avatar.setRadius(24)
            self.avatar.move(2, 6)
            self.nameLabel.move(64, 13)
            self.emailLabel.move(64, 32)

    def createProfileWidget(self, e, name='zhiyoko', email='shokokawaii@outlook.com', avatarPath='resources/shoko.png'):
        menu = RoundMenu(self)
        card = self.ProfileCard(avatarPath, name, email, menu)
        menu.addWidget(card, selectable=False)

        menu.addSeparator()
        menu.addActions([
            Action(FluentIcon.PEOPLE, 'Manage Account'),
            Action(FluentIcon.CANCEL, 'Logout'),
        ])
        menu.addSeparator()
        menu.addAction(Action(FluentIcon.SETTING, 'Settings'))

        self.menu = menu
        menu.exec(e.globalPos())

class Main(FluentWindow):

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
    app.exec_()

if __name__ == '__main__':
    show()
