import sys

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QIcon, QImage, QPainter, QPainterPath
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame, QSizePolicy, \
    QApplication, QHBoxLayout
from qfluentwidgets import (CardWidget, HeaderCardWidget, SplitTitleBar, isDarkTheme, CommandBar, Action, FluentIcon,
                            FlyoutViewBase, Slider, CaptionLabel, Flyout, FlyoutAnimationType,
                            AvatarWidget, SingleDirectionScrollArea, TextEdit, PrimaryToolButton
                            )
from qfluentwidgets.components.widgets.card_widget import CardSeparator


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


if isWin11():
    from qframelesswindow import AcrylicWindow as MeetingWindow
else:
    from qframelesswindow import FramelessWindow as MeetingWindow

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

        # self.set_image(QImage(":/images/background.jpg"))
        self.setSpeaker("ZhiyiYo")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.init_brush()


    def defaultImage(self):
        w, h = self.width() if self.width() > 0 else 960, self.height() if self.height() > 0 else 540
        image = QImage(w, h, QImage.Format_RGB32)
        image.fill(Qt.white)
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

    def setSpeaker(self, name):
        self.speakerLabel.setName(name)

    def fit_image(self, image):
        w, h = self.width(), self.height()
        # resize the image to fit the height of the widget, add black padding to the left and right
        image = image.scaledToHeight(h, Qt.SmoothTransformation)

        if image.width() < w:
            padding = QImage(w, h, QImage.Format_RGB32)
            padding.fill(Qt.black)
            painter = QPainter(padding)
            painter.drawImage((w - image.width()) // 2, 0, image)
            painter.end()
            image = padding

        return image


    def paintEvent(self, e):
        self.painter.begin(self)
        self.painter.setClipPath(self.painterPath)
        self.painter.drawImage(self.rect(), self.currentImage)
        self.painter.end()

class VolumeFlyout(FlyoutViewBase):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.slider = Slider(Qt.Vertical, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)

        self.volHint = CaptionLabel(str(self.slider.value()), self)
        self.volHint.setAlignment(Qt.AlignCenter)
        self.mainLayout.addWidget(self.volHint, alignment=Qt.AlignCenter)

        self.mainLayout.addWidget(self.slider, alignment=Qt.AlignCenter)
        self.setFixedSize(50, 120)




class FullCommandBar(CommandBar):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.addActions([
            Action(FluentIcon.SHARE, 'Share', triggered=self.share),
            Action(FluentIcon.MICROPHONE, 'Speak', triggered=self.speak),
            Action(FluentIcon.MUTE, 'Mute', triggered=self.mute),
            Action(FluentIcon.VOLUME, 'Volume', triggered=self.volume)
        ])

        self.addSeparator()

        self.addActions([
            Action(FluentIcon.RETURN, 'Leave', triggered=self.leave),
            Action(FluentIcon.DELETE, 'Cancel', triggered=self.end)
        ])

        self.resizeToSuitableWidth()

    def getAction(self, key):
        """
        Get the action by key
        """
        for action in self.actions():
            if action.text() == key:
                return action

    def share(self):
        pass

    def speak(self):
        pass

    def mute(self):
        pass

    def volume(self):
        flyout = VolumeFlyout(self)
        Flyout.make(
            flyout,
            self,
            self,
            aniType=FlyoutAnimationType.PULL_UP
        )

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
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setTitle("Chat")

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.setMinimumSize(260, 400)
        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setContentsMargins(0, 0, 0, 0)
        self.bottomLayout.setSpacing(0)

        self.textEdit = TextEdit(self)
        self.textEdit.setPlaceholderText("Type your message here")
        self.textEdit.setFixedHeight(70)
        self.textEdit.setFixedWidth(200)

        self.sendButton = PrimaryToolButton(self)
        self.sendButton.setFixedSize(60, 70)
        self.sendButton.setIcon(FluentIcon.SEND)

        self.bottomLayout.addWidget(self.textEdit, alignment=Qt.AlignCenter)
        self.bottomLayout.addWidget(self.sendButton, alignment=Qt.AlignCenter)

        self.mainLayout.addStretch(1)
        self.mainLayout.addWidget(CardSeparator(self))
        self.mainLayout.addLayout(self.bottomLayout)


        self.viewLayout.addLayout(self.mainLayout)

class MeetingInterfaceBase(MeetingWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # set up sub widgets
        self.title = ""
        self.displayArea = ViewWidget(self)
        self.participantsArea = ParticipantCardView(self)
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


    def resizeEvent(self, e):
        super().resizeEvent(e)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MeetingInterfaceBase()
    window.show()
    sys.exit(app.exec_())
