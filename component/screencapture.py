from enum import Enum
from tkinter.ttk import Combobox

import PIL.Image
import psutil
import win32con
import win32gui
import win32process
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QWindow, QScreen
from PyQt5.QtWidgets import QFrame, QVBoxLayout
from qfluentwidgets import CommandBarView, BodyLabel, Action, FluentIcon, CommandBar, MessageBox, MessageBoxBase, \
    ComboBox, SubtitleLabel


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

    def getType(self):
        return self.mode

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

    def __init__(self, parent=None):
        super().__init__(parent)
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

        # # display upper CommandBar
        # # self.mainLayout = QVBoxLayout(self)
        # self.command_bar = RegionSelectorCommandBar(self)
        # self.command_bar.canceled.connect(self.close)
        # self.command_bar.confirmed.connect(self.handle_confirm)

        # # Layout
        # self.mainLayout = QVBoxLayout(self)
        # self.mainLayout.addWidget(self.command_bar)
        # self.mainLayout.setContentsMargins(0, 0, 0, 0)
        # self.setLayout(self.mainLayout)

    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        self.end_pos = event.pos()
        self.selection_rect = QRect()
        self.update()

    def mouseMoveEvent(self, event):
        self.end_pos = event.pos()
        self.selection_rect = QRect(self.start_pos, self.end_pos).normalized()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.end_pos = event.pos()
            self.selection_rect = QRect(self.start_pos, self.end_pos).normalized()
            self.update()

    def handle_confirm(self):
        if self.selection_rect.width() == 0 or self.selection_rect.height() == 0:
            return

        result = (Result(CaptureMode.REGION)
                  .setRegion(self.selection_rect.x(), self.selection_rect.y(), self.selection_rect.width(), self.selection_rect.height()))
        print("Region selected", result.unpack())
        self.result_returned.emit(result)

        self.setWindowState(Qt.WindowNoState)
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

        # Draw the background
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.setPen(QPen(Qt.transparent))
        painter.drawRect(self.rect())

        # Render the selection rect
        if not self.selection_rect.isNull():
            painter.setBrush(QBrush(Qt.transparent))
            painter.setPen(QPen(Qt.yellow, 2))
            painter.drawRect(self.selection_rect)

    def closeEvent(self, a0):
        self.setWindowState(Qt.WindowNoState)
        super().closeEvent(a0)
        a0.accept()


    ### Window Selector ###
class WindowSelector(MessageBoxBase):

    result_returned = pyqtSignal(Result)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Select Window to Capture")

        self._label = SubtitleLabel("Select a window to capture", parent=self)
        self._window_list_dropdown = ComboBox(parent=parent)
        self._window_list_dropdown.setPlaceholderText("Select a window")
        self._window_list_dropdown.setCurrentIndex(-1)
        self._map = {} # {index: window_id}

        self.update_window_list()

        self._window_list_dropdown.clicked.connect(self.update_window_list)

        self.viewLayout.addWidget(self._label)
        self.viewLayout.addWidget(self._window_list_dropdown)

        self.widget.setFixedSize(400, 220)

    def update_window_list(self):
        self._window_list_dropdown.clear()
        self._map.clear()

        windows = get_active_windows()
        for index, window in enumerate(windows):
            self._window_list_dropdown.addItem(f"{window['title']} - {window['process_name']}")
            self._map[index] = window['hwnd']

    def handle_window_selected(self):
        currentIndex = self._window_list_dropdown.currentIndex()
        if currentIndex == -1:
            return
        else:
            window_id = self._map[currentIndex]
            result = (Result(CaptureMode.WINDOW).setWindow(window_id))
            print("Window selected", result.unpack())
            self.result_returned.emit(result)

    def validate(self) -> bool:
        if self._window_list_dropdown.currentIndex() == -1:
            return False
        else:
            self.handle_window_selected()
            return True

    def closeEvent(self, a0):
        super().closeEvent(a0)
        a0.accept()


def get_active_windows():
    """get all active windows"""
    windows = []

    def callback(hwnd, extra):
        # 获取窗口标题
        title = win32gui.GetWindowText(hwnd)

        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if ex_style & win32con.WS_EX_TOOLWINDOW:
            return

        # 检查窗口是否可见且有标题
        if win32gui.IsWindowVisible(hwnd) and title and win32gui.IsWindowEnabled(hwnd):
            # 获取窗口所属进程 ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            # 获取进程名称
            try:
                process_name = psutil.Process(pid).name()

                if process_name in ["SystemSettingsBroker.exe", "SystemSettings.exe", "ApplicationFrameHost.exe", "TextInputHost.exe"]:
                    return
            except psutil.NoSuchProcess:
                process_name = "Unknown"
            # 保存窗口信息
            windows.append({
                "hwnd": hwnd,
                "title": title,
                "process_name": process_name,
                "pid": pid
            })

    # 枚举所有顶层窗口
    win32gui.EnumWindows(callback, None)
    return windows

class ScreenCapture:
    def __init__(self):
        pass

    def capture(self) -> PIL.Image:
        pass

class WindowCapture(ScreenCapture):
    def __init__(self, window_id: int = None):
        super().__init__()
        self.window_id = window_id

    def capture(self) -> PIL.Image:
        if self.window_id:
            screen = QApplication.primaryScreen()
            image = screen.grabWindow(self.window_id).toImage()
            return image

class RegionCapture(ScreenCapture):
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def capture(self) -> PIL.Image:
        screen = QApplication.primaryScreen()
        image = screen.grabWindow(QWindow().winId(), self.x, self.y, self.width, self.height).toImage()
        return image

class FullScreenCapture(ScreenCapture):
    def __init__(self):
        super().__init__()

    def capture(self) -> PIL.Image:
        screen = QApplication.primaryScreen()
        image = screen.grabWindow(QWindow().winId()).toImage()
        return image

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    #
    app = QApplication(sys.argv)
    window = MaskedRegionSelector()

    window.show()
    sys.exit(app.exec_())
    # frame = QFrame()
    # frame.resize(800, 600)
    # message_box = WindowSelector(frame)
    # frame.show()
    # if message_box.exec():
    #     print(message_box.result_returned)
    #     sys.exit(0)
    # else:
    #     sys.exit(1)

