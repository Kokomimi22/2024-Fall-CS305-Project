from enum import Enum

from PyQt5.QtCore import Qt, pyqtSignal, QRect, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush
from PyQt5.QtWidgets import QFrame, QVBoxLayout
from qfluentwidgets import CommandBarView, BodyLabel, Action, FluentIcon, CommandBar


class CaptureMode(Enum):
    FULL_SCREEN = 1
    WINDOW = 2
    REGION = 3

class Result:
    def __init__(self, mode: CaptureMode):
        self.mode = mode

        # for region mode
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

        # for window mode
        self.window_id = 0

    def setRegion(self, x, y, width, height):
        if self.mode != CaptureMode.REGION:
            raise ValueError("Region mode is not enabled")
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        return self

    def setWindow(self, window_id):
        if self.mode != CaptureMode.WINDOW:
            raise ValueError("Window mode is not enabled")
        self.window_id = window_id
        return self

    def unpack(self):
        """
        Returns the unpacked data based on the mode
        """
        if self.mode == CaptureMode.FULL_SCREEN:
            return None
        elif self.mode == CaptureMode.WINDOW:
            return self.window_id
        elif self.mode == CaptureMode.REGION:
            return self.x, self.y, self.width, self.height
        else:
            raise ValueError("Invalid mode")


    ### Region Selector ###

class RegionSelectorCommandBar(CommandBar):

    confirmed = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._size_hint_label = BodyLabel() # display the current selection size (width x height)
        self._confirm_action = Action(FluentIcon.ACCEPT_MEDIUM.colored(Qt.green, Qt.green), "Confirm", triggered=self.confirmed.emit)
        self._cancel_action = Action(FluentIcon.CANCEL_MEDIUM.colored(Qt.red, Qt.red), "Cancel", triggered=self.canceled.emit)

        self.addWidget(self._size_hint_label)
        self.addSeparator()
        self.addAction(self._cancel_action)
        # hide the confirm button

        self.resizeToSuitableWidth()

    def setSelectionSize(self, width, height):
        self._size_hint_label.setText(f"{width} x {height}")

    def setConfirmVisible(self, visible):
        self._confirm_action.setVisible(visible)

class MaskedRegionSelector(QFrame):

    result_returned = pyqtSignal(Result)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # for region mode
        self.start_pos = None
        self.end_pos = None
        self.selection_rect = QRect()

        # display upper CommandBar
        self.mainLayout = QVBoxLayout()
        self.command_bar = RegionSelectorCommandBar()
        self.command_bar.canceled.connect(self.close)
        self.command_bar.confirmed.connect(self.handle_confirm)

        self.mainLayout.addWidget(self.command_bar)

    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        self.end_pos = event.pos()
        self.selection_rect = QRect()
        self.command_bar.setConfirmVisible(False)
        self.update()

    def mouseMoveEvent(self, event):
        self.end_pos = event.pos()
        self.selection_rect = QRect(self.start_pos, self.end_pos).normalized()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.end_pos = event.pos()
            self.selection_rect = QRect(self.start_pos, self.end_pos).normalized()
            self.command_bar.setConfirmVisible(True)
            self.update()

    def handle_confirm(self):
        if self.selection_rect.width() == 0 or self.selection_rect.height() == 0:
            return

        result = (Result(CaptureMode.REGION)
                  .setRegion(self.selection_rect.x(), self.selection_rect.y(), self.selection_rect.width(), self.selection_rect.height()))
        self.result_returned.emit(result)

        self.close()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key_Escape:
            print("Cancel region selection")
            self.close()
        elif a0.key() == Qt.Key_Return:
            self.handle_confirm()
            print("Confirm region selection")
        else:
            super().keyPressEvent(a0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # paint the background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

        # render the selection rect
        if not self.selection_rect.isNull():
            # remove the mask in the selection rect
            painter.setBrush(QBrush(Qt.transparent))
            painter.setPen(QPen(Qt.yellow, 2))
            painter.drawRect(self.selection_rect)

    def closeEvent(self, a0):
        super().closeEvent(a0)
        print("Region selector closed")


    ### Window Selector ###


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MaskedRegionSelector()
    window.show()
    sys.exit(app.exec())
