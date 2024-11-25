from PyQt5.QtCore import Qt
from qfluentwidgets import SingleDirectionScrollArea, TogglePushButton, HeaderCardWidget, FluentIcon, TitleLabel, \
    ComboBox, SmoothScrollArea, ProgressBar, CardWidget, BodyLabel, ImageLabel, CaptionLabel
from qfluentwidgets.multimedia.media_play_bar import PlayButton, VolumeButton, FluentStyleSheet
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QSpacerItem, QSizePolicy


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