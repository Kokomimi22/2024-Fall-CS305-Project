import math
import sys
from enum import Enum

from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QImage, QPainter, QPainterPath
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame, QSizePolicy, \
    QApplication, QHBoxLayout, QPushButton, QTextBrowser, QActionGroup
from qfluentwidgets import (CardWidget, HeaderCardWidget, SplitTitleBar, isDarkTheme, CommandBar, Action, FluentIcon,
                            FlyoutViewBase, Slider, CaptionLabel, Flyout, FlyoutAnimationType,
                            AvatarWidget, SingleDirectionScrollArea, TextEdit, PrimaryToolButton, TextBrowser,
                            MessageDialog, MessageBox, RoundMenu, SmoothScrollArea, BodyLabel, PrimaryPushButton,
                            TransparentToolButton, ToolButton, InfoBar, InfoBarPosition, CheckableMenu,
                            TransparentPushButton, ToolTipFilter, MenuIndicatorType, TransparentDropDownPushButton,
                            FluentIconBase, Theme
                            )
from qfluentwidgets.components.widgets.card_widget import CardSeparator
from qfluentwidgets.components.widgets.flyout import IconWidget, PullUpFlyoutAnimationManager
from qfluentwidgets.multimedia.media_play_bar import VolumeButton, VolumeView
from typing_extensions import override, overload

from resources import rc


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


if isWin11():
    from qframelesswindow import AcrylicWindow as MeetingWindow
else:
    from qframelesswindow import FramelessWindow as MeetingWindow

class MeetingIcon(FluentIconBase, Enum):
    STOP_SPEAK = "mute"

    def path(self, theme=Theme.AUTO) -> str:
        return f":/icon/{self.value}.png"


class MeetingTitleBar(SplitTitleBar):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # set the style of the title bar button
        self.minBtn.setHoverColor(Qt.white)
        self.minBtn.setHoverBackgroundColor(QColor(0, 100, 182))
        self.minBtn.setPressedColor(Qt.white)
        self.minBtn.setPressedBackgroundColor(QColor(54, 57, 65))

        # use qss to customize title bar button
        self.maxBtn.setStyleSheet("""
            TitleBarButton {
                qproperty-normalColor: black;
                qproperty-normalBackgroundColor: transparent;
                qproperty-hoverColor: white;
                qproperty-hoverBackgroundColor: rgb(0, 100, 182);
                qproperty-pressedColor: white;
                qproperty-pressedBackgroundColor: rgb(54, 57, 65);
            }
        """)

class SpeakerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setObjectName("SpeakerWidget")

        font = QFont()
        font.setPixelSize(12)
        font.setFamilies(["Segoe UI", "Microsoft YaHei"])

        self.nameLabel = QLabel(self)
        self.nameLabel.setFont(font)
        self.nameLabel.setMaximumWidth(150)
        self.nameLabel.setFixedHeight(15)
        self.nameLabel.setWordWrap(True)

        self.setFixedHeight(20)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.nameLabel)

        self.setStyleSheet("""
            QLabel {
                color: white;
                background: rgba(0, 0, 0, 0.5);
            }
        """)

    def setName(self, name):
        self.nameLabel.setText(name)

class ViewWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setMinimumSize(960, 540) # 16:9

        self.speakerLabel = SpeakerWidget(self) # bottom right corner
        self.painter = None # QPainter
        self.currentImage = self.defaultImage() # QImage
        self.painterPath = None # QPainterPath

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 4, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.speakerLabel, 0, Qt.AlignBottom | Qt.AlignRight)

        self.setSpeaker("Default")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.init_brush()


    def defaultImage(self):
        w, h = self.width() if self.width() > 0 else 960, self.height() if self.height() > 0 else 540
        image = QImage(w, h, QImage.Format_RGB32)
        image.fill(Qt.black)
        return image

    def setToDefault(self):
        self.currentImage = self.defaultImage()
        self.update()

    def init_brush(self):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)
        self.painter = painter

        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        # draw the rounded rectangle with 8 radius
        path.addRoundedRect(QRectF(self.rect()), 8, 8)
        path = path.simplified()

        self.painterPath = path


    def set_image(self, image):
        self.currentImage = self.fit_image(image)
        self.update()

    def setSpeaker(self, name):
        self.speakerLabel.setName(name)

    def fit_image(self, image):
        w, h = self.width(), self.height()
        # resize the image to fit the height of the widget, add black padding to the left and right
        if image.height() == h and image.width() == w:
            return image

        image = image.scaledToHeight(h, Qt.SmoothTransformation)

        if image.width() < w:
            padding = QImage(w, h, QImage.Format_RGB32)
            padding.fill(Qt.black)
            painter = QPainter(padding)
            painter.drawImage((w - image.width()) // 2, 0, image)
            painter.end()
            image = padding
        elif image.width() == w:
            pass
        else:
            image = image.scaledToWidth(w, Qt.SmoothTransformation)
            padding = QImage(w, h, QImage.Format_RGB32)
            padding.fill(Qt.black)
            painter = QPainter(padding)
            painter.drawImage(0, (h - image.height()) // 2, image)
            painter.end()
            image = padding
        return image


    def paintEvent(self, e):
        self.painter.begin(self)
        self.painter.setClipPath(self.painterPath)
        self.painter.drawImage(self.rect(), self.currentImage)
        self.painter.end()

class LabelledVolumeButton(TransparentPushButton):
    """ Volume button """

    volumeChanged = pyqtSignal(int)
    mutedChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText('Volume')
        self.setFont(QFont('Segoe UI', 9))
        self.volumeView.volumeLabel.hide()

    def _postInit(self):
        super()._postInit()
        self.installEventFilter(ToolTipFilter(self, 1000))
        self.setFixedSize(90, 30)
        self.setIconSize(QSize(16, 16))

        self.volumeView = VolumeView(self)
        self.volumeFlyout = Flyout(self.volumeView, self.window(), False)
        self.setMuted(False)

        self.volumeFlyout.hide()
        self.volumeView.muteButton.clicked.connect(lambda: self.mutedChanged.emit(not self.isMuted))
        self.volumeView.volumeSlider.valueChanged.connect(self.volumeChanged)
        self.clicked.connect(self._showVolumeFlyout)

    def setMuted(self, isMute: bool):
        self.isMuted = isMute
        self.volumeView.setMuted(isMute)

        if isMute:
            self.setIcon(FluentIcon.MUTE)
        else:
            self.setIcon(FluentIcon.VOLUME)

    def setVolume(self, volume: int):
        self.volumeView.setVolume(volume)

    def _showVolumeFlyout(self):
        if self.volumeFlyout.isVisible():
            return

        pos = PullUpFlyoutAnimationManager(self.volumeFlyout).position(self)
        self.volumeFlyout.exec(pos)


class FullCommandBar(CommandBar):

    share_signal = pyqtSignal(str)
    speak_signal = pyqtSignal(bool)
    quit_signal = pyqtSignal()
    cancel_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.share_action = TransparentDropDownPushButton(FluentIcon.SHARE, 'Share')
        self.share_action.setFixedSize(100, 30)
        self.share_action.setFont(QFont('Segoe UI', 9))
        self.speak_action = Action(MeetingIcon.STOP_SPEAK, 'Speak')

        self.addWidget(self.share_action)
        self.addActions([
            self.speak_action,
        ])
        self.volume_action = LabelledVolumeButton(self)
        self.addWidget(self.volume_action)

        self.share_menu = CheckableMenu(self, indicatorType=MenuIndicatorType.RADIO)
        self._init_share_menu()
        self.share_action.setMenu(self.share_menu)

        self.addSeparator()

        self.addActions([
            Action(FluentIcon.RETURN, 'Leave', triggered=lambda : self.quit_signal.emit()),
            Action(FluentIcon.DELETE, 'Cancel', triggered=lambda : self.cancel_signal.emit())
        ])

        self.resizeToSuitableWidth()

    def _init_share_menu(self):
        actionGroup = QActionGroup(self)
        actionGroup.setExclusive(True)

        action1 = Action(FluentIcon.PAUSE, 'Don\'t Share', triggered=lambda : self.share_signal.emit('stop'), checkable=True)
        action2 = Action(FluentIcon.VIDEO, 'Screen', triggered=lambda : self.share_signal.emit('screen'), checkable=True)
        action3 = Action(FluentIcon.CAMERA, 'Camera', triggered=lambda : self.share_signal.emit('camera'), checkable=True)
        actionGroup.addAction(action1)
        actionGroup.addAction(action2)
        actionGroup.addAction(action3)

        self.share_menu.addActions([
            action1, action2, action3
        ])

        action1.setChecked(True)

    def setSpeak(self, isSpeaking):
        self.speak_action.setIcon(FluentIcon.MICROPHONE if isSpeaking else MeetingIcon.STOP_SPEAK)

    def share_menu_event(self, checked):
        if checked:
            pos = self.mapToGlobal(self.sender().pos())
            self.share_menu.exec(pos)

    def getAction(self, key):
        """
        Get the action by key
        """
        for action in self.actions():
            if action.text() == key:
                return action

    def removeActionByKey(self, key: str):
        action = self.getAction(key)
        if action:
            self.removeAction(action)
        self.resizeToSuitableWidth()

    def share(self):
        pass

    def speak(self):
        pass

    def mute(self):
        pass

    def volume(self):
        pass

    def leave(self):
        pass

    def end(self):
        pass


class CommandBarCard(CardWidget):
    def __init__(self, commandBar, parent=None):
        super().__init__(parent=parent)
        assert isinstance(commandBar, CommandBar)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 5, 0, 5)

        self.commandBar = commandBar
        self.mainLayout.addWidget(self.commandBar, alignment=Qt.AlignCenter)
        iw, ih = self.commandBar.width(), self.commandBar.height()

        self.setFixedSize(iw + 15, ih + 10)

    def getCommandBar(self):
        return self.commandBar

    def removeActionByKey(self, key: str):
        self.commandBar.removeActionByKey(key)
        iw, ih = self.commandBar.width(), self.commandBar.height()
        self.setFixedSize(iw + 15, ih + 10)

class ParticipantCardView(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setTitle("Participants")

        self.scrollView = SingleDirectionScrollArea(self, Qt.Vertical)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 40, 0, 0)

        # initial the layout for participants
        self.participantGrid = QFrame()
        self.participantGrid.setObjectName("ParticipantGrid")

        self.scrollView.setWidget(self.participantGrid)
        self.scrollView.enableTransparentBackground()

        self.bodyLayout = QGridLayout(self.participantGrid)
        self.bodyLayout.setContentsMargins(0, 0, 0, 0)
        self.bodyLayout.setSpacing(10)

        self.mainLayout.addStretch(1)
        self.mainLayout.addWidget(self.scrollView, alignment=Qt.AlignCenter)

        self.participantUnit = [] # list['ViewUnit']

        self.setMinimumSize(260, 300)

        self.scrollView.move(5, 50)


    def addUnit(self, name, avatar_img):
        unit = self.ViewUnit(name, avatar_img, self.participantGrid)
        unit.setFixedSize(70, 70)
        self.bodyLayout.addWidget(unit, self.bodyLayout.rowCount(), 0, alignment=Qt.AlignCenter)
        self.participantUnit.append(unit)
        self.update()

    class ViewUnit(QFrame):
        def __init__(self, name, avatar_img, parent=None):
            super().__init__(parent=parent)

            self.mainLayout = QVBoxLayout(self)
            self.mainLayout.setContentsMargins(0, 0, 0, 0)
            self.mainLayout.setSpacing(3)

            self.avatar = AvatarWidget(avatar_img, self)
            self.avatar.setRadius(24)

            self.nameLabel = CaptionLabel(name, self)

            self.mainLayout.addWidget(self.avatar, alignment=Qt.AlignCenter)
            self.mainLayout.addWidget(self.nameLabel, alignment=Qt.AlignCenter)

            self.setFixedSize(70, 70)
            self.setStyleSheet("""
                QLabel {
                    background: transparent;
                }
            """)

class ChatCardView(HeaderCardWidget):

    MAX_MESSAGE = 50

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setTitle("Chat")

        self.damakuList = [] # type: list['DamakuWidget']

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.setMinimumSize(260, 400)
        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.chatWidget = QWidget()
        self.chatWidget.setObjectName("ChatWidget")
        self.chatWidget.setFixedWidth(260)
        self.chatWidget.setMinimumHeight(50)
        self.chatWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chatArea = SmoothScrollArea(self)
        self.chatArea.setWidget(self.chatWidget)
        self.chatArea.enableTransparentBackground()

        self.chatAreaLayout = QVBoxLayout(self.chatWidget)
        self.chatAreaLayout.setContentsMargins(0, 0, 0, 0)
        self.chatAreaLayout.setSpacing(5)

        self.pullDownButton = ToolButton(self)
        self.pullDownButton.setIcon(FluentIcon.DOWN)
        self.pullDownButton.setFixedSize(25, 25)
        self.pullDownButton.move(115, 300)
        self.pullDownButton.hide()

        self.chatArea.setFixedSize(260, 270)
        self.mainLayout.addWidget(self.chatArea, alignment=Qt.AlignCenter)

        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setContentsMargins(0, 0, 0, 0)
        self.bottomLayout.setSpacing(0)

        self.textEdit = TextEdit(self)
        self.textEdit.setPlaceholderText("Type your message here")
        self.textEdit.setFixedHeight(70)
        self.textEdit.setFixedWidth(200)

        self.textEdit.textChanged.connect(self.handle_text_changed)

        self.sendButton = PrimaryToolButton(self)
        self.sendButton.setFixedSize(60, 70)
        self.sendButton.setIcon(FluentIcon.SEND)
        self.sendButton.setEnabled(False)

        self.bottomLayout.addWidget(self.textEdit, alignment=Qt.AlignCenter)
        self.bottomLayout.addWidget(self.sendButton, alignment=Qt.AlignCenter)

        self.mainLayout.addStretch(1)
        self.separator = CardSeparator(self)

        self.mainLayout.addWidget(self.separator)
        self.mainLayout.addLayout(self.bottomLayout)

        self.viewLayout.addLayout(self.mainLayout)

        self.chatArea.verticalScrollBar().valueChanged.connect(self.handle_scroll_up)
        self.pullDownButton.clicked.connect(self.scroll_to_bottom)

        self.scroll_value_temp = 0
        self.chatArea_pref_height = 0
    
    def addMessage(self, name, message, timestamp):
        damaku = self.DamakuWidget(name, message, timestamp=timestamp, parent=self)
        self.chatAreaLayout.addWidget(damaku)
        self.chatArea_pref_height += damaku.height() + 5
        self.chatWidget.setFixedHeight(self.chatArea_pref_height)
        self.damakuList.append(damaku)
        if self.damakuList.__len__() > self.MAX_MESSAGE:
            damaku = self.damakuList.pop(0)
            self.chatAreaLayout.removeWidget(damaku)
            damaku.deleteLater()
            self.chatArea_pref_height -= damaku.height() + 5
            self.chatWidget.setFixedHeight(self.chatArea_pref_height)
        self.scroll_to_bottom()

    def handle_text_changed(self):
        text = self.textEdit.toPlainText()
        if text:
            self.sendButton.setEnabled(True)
        else:
            self.sendButton.setEnabled(False)

    def text_edit_clear(self):
        self.textEdit.clear()
        self.sendButton.setEnabled(False)

    def handle_scroll_up(self, cur_val):
        max_val = self.chatArea.verticalScrollBar().maximum()
        if cur_val == max_val:
            self.scroll_value_temp = cur_val
            self.pullDownButton.hide()
        elif abs(cur_val - self.scroll_value_temp) > 100:
            self.scroll_value_temp = cur_val
            self.pullDownButton.show()

    def scroll_to_bottom(self):
        self.chatArea.verticalScrollBar().setValue(self.chatArea.verticalScrollBar().maximum())

    class DamakuWidget(QWidget):
        """
        A damaku widget that shows single message from the chat
        """
        trash_signal = pyqtSignal()

        def __init__(self, name, message, timestamp="hh:mm:ss", parent=None):
            super().__init__()
            self.setFixedWidth(260)

            self.mainLayout = QHBoxLayout(self)
            self.mainLayout.setContentsMargins(5, 0, 5, 0)
            self.mainLayout.setSpacing(0)

            self.textDisplay = BodyLabel(self)
            self.textDisplay.setFixedWidth(250)

            self.mainLayout.addWidget(self.textDisplay, alignment=Qt.AlignCenter)

            # set the style of the text display
            self.textDisplay.setStyleSheet("""
                QLabel {
                    background: transparent;
                    color: black;
                }
                QLabel:hover {
                    background: rgba(0, 0, 0, 0.1);
                    }
            """)

            self.textDisplay.setText(f"<span style='color: #707070; font-weight: 500;'>{name}</span>&nbsp;&nbsp; <span>{self.convert_plain_text(message)}</span>")
            self.textDisplay.setMinimumHeight(25)
            self.textDisplay.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            self.textDisplay.setWordWrap(True)

            self.roundMenu = RoundMenu(self)

            self.trashAction = Action(FluentIcon.DELETE, 'Delete', triggered=lambda: self.trash_signal.emit())
            self.copyAction = Action(FluentIcon.COPY, 'Copy', triggered=lambda: self.copy())

            self.setMinimumHeight(25)
            self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            self.adjustSize()

            self.defaultText = f"<span style='color: #707070; font-weight: 500;'>{name}</span>&nbsp;&nbsp; <span>{self.convert_plain_text(message)}</span>"
            self.timestamp = f"&nbsp;&nbsp; <span style='color:#a6a6a6; font-weight: 350;'>{timestamp}</span>"

        def enterEvent(self, e):
            """show hiden timestamp"""
            self.textDisplay.setText(self.defaultText + self.timestamp)

        def leaveEvent(self, e):
            """hide timestamp"""
            self.textDisplay.setText(self.defaultText)

        @staticmethod
        def convert_plain_text(text):
            """
            convert '\n' to '<br />' in plain text
            """
            return text.replace('\n', '<br />')


class MeetingInterfaceBase(MeetingWindow):

    close_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # set up sub widgets
        self.displayArea = ViewWidget(self)
        self.participantsArea = ParticipantCardView(self)
        self.participantsArea.hide()
        self.chatArea = ChatCardView(self)
        self.commandBar = CommandBarCard(FullCommandBar(self))

        self.mainLayout = QHBoxLayout(self)

        self.setTitleBar(MeetingTitleBar(self))
        self.titleBar.raise_()

        self.setWindowIcon(QIcon(":/images/logo.png"))

        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=isDarkTheme())
        if not isWin11():
            color = QColor(25, 33, 42) if isDarkTheme() else QColor(240, 244, 249)
            self.setStyleSheet(f"LoginWindow{{background: {color.name()}}}")

        if sys.platform == "darwin":
            self.setSystemTitleBarButtonVisible(True)
            self.titleBar.minBtn.hide()
            self.titleBar.maxBtn.hide()
            self.titleBar.closeBtn.hide()

        self.titleBar.titleLabel.setStyleSheet("""
            QLabel{
                background: transparent;
                font: 13px 'Segoe UI';
                padding: 0 4px;
                color: white
            }
        """)

        self.set_up()
        self.setMinimumSize(1280, 720)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def set_up(self):
        self.mainLayout.setContentsMargins(20, 40, 20, 20)
        self.mainLayout.setSpacing(0)

        leftBox = QVBoxLayout()
        leftBox.setSpacing(20)
        rightBox = QVBoxLayout()

        leftBox.addStretch(1)
        leftBox.addWidget(self.displayArea, alignment=Qt.AlignCenter, stretch=1)
        leftBox.addWidget(self.commandBar, alignment=Qt.AlignCenter, stretch=0)
        leftBox.addStretch(1)

        rightBox.addStretch(1)
        rightBox.addWidget(self.participantsArea, alignment=Qt.AlignCenter, stretch=1)
        rightBox.addWidget(self.chatArea, alignment=Qt.AlignCenter, stretch=0)
        rightBox.addStretch(1)
        rightBox.setSpacing(10)

        self.mainLayout.addStretch(1)
        self.mainLayout.addLayout(leftBox, stretch=1)
        self.mainLayout.addLayout(rightBox, stretch=1)
        self.mainLayout.addStretch(1)
        self.mainLayout.setSpacing(20)

    def setTitle(self, title):
        self.titleBar.titleLabel.setText(title)
        self.titleBar.titleLabel.setStyleSheet("""
            QLabel{
                background: transparent;
                color: black;
            }
        """)

    def resizeEvent(self, e):
        super().resizeEvent(e)

    def messageBox(self):
        dialog = MessageBox('Are you sure to leave the meeting?',
                               '',
                               parent=self)
        return dialog

    def closeEvent(self, e):
        w = self.messageBox()
        if w.exec():
            self.close_signal.emit()
            e.accept()
        else:
            e.ignore()

    def info(self, info_level, title, msg, pos=InfoBarPosition.TOP, orient=Qt.Orientation.Horizontal):
        """
        generate toast-like infobar
        """
        if info_level == 'success':
            InfoBar.success(
                title=title,
                content=msg,
                orient=orient,
                isClosable=True,
                duration=3000,
                position=pos,
                parent=self
            )
        elif info_level == 'warning':
            InfoBar.warning(
                title=title,
                content=msg,
                orient=orient,
                isClosable=True,
                duration=3000,
                position=pos,
                parent=self
            )
        elif info_level == 'error':
            InfoBar.error(
                title=title,
                content=msg,
                orient=orient,
                isClosable=True,
                duration=3000,
                position=pos,
                parent=self
            )
        elif info_level == 'info':
            InfoBar.info(
                title=title,
                content=msg,
                orient=orient,
                isClosable=True,
                duration=3000,
                position=pos,
                parent=self
            )
        else:
            raise ValueError('Invalid info_level')

class SimpleMeetingInterface(MeetingInterfaceBase):
    """
    Meeting interface for single type meeting (non-owned single type)
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.commandBar.removeActionByKey('Cancel')

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    window = MeetingInterfaceBase()
    window.show()
    sys.exit(app.exec_())
