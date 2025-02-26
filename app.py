import atexit
import json
import sys
import traceback

from PIL.Image import Image
from PyQt5.QtCore import pyqtSignal, QObject

from common.conf_client import ConferenceClient
from component.audiopreview import AudioPreview
from component.meetingcardgroup import MeetingCardsGroupHandler
from component.meetingcontroller import MeetingController
from component.meetingcreate import MeetingCreate
from component.videopreview import VideoPreview
from config import *
from view.gui import LoginWindow
from view.gui import Main
from view.gui import TestInterface
from view.homescreen import HomeInterface
from view.meetingscreen import MeetingInterfaceBase, SimpleMeetingInterface


class AppConfig:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        self.username_cache = None
        self.password_cache = None
        # ...

    @classmethod
    def setUsernameCache(cls, username):
        cls._instance.username_cache = username

    @classmethod
    def setPasswordCache(cls, password):
        cls._instance.password_cache = password

    @classmethod
    def usernameCache(cls):
        return cls._instance.username_cache

    @classmethod
    def passwordCache(cls):
        return cls._instance.password_cache

    @classmethod
    def clearCache(cls):
        cls._instance.username_cache = None
        cls._instance.password_cache = None
        # ...

    @classmethod
    def save(cls):
        with open(CONFIG_INFO_FILE, 'w') as f:
            data = {
                'username': cls._instance.username_cache,
                'password': cls._instance.password_cache
            }
            json.dump(data, f, indent=4)

    @staticmethod
    def load():
        try:
            with open(CONFIG_INFO_FILE, 'r') as f:
                data = json.load(f)
                config = AppConfig()
                config.username_cache = data.get('username')
                config.password_cache = data.get('password')
                return config
        except FileNotFoundError:
            print('No config file found, initializing...')
            return AppConfig()


class AppController(QObject):

    closed = pyqtSignal()
    message_received = pyqtSignal(str, str, str)  # sender_name, message, timestamp
    video_received = pyqtSignal(Image)  # video
    control_received = pyqtSignal(MessageType, str)  # for control message

    def __init__(self, mainui: Main, loginui: LoginWindow):
        super().__init__()
        AppConfig.load()

        self.mainui = mainui
        self.loginui = loginui
        self.logincontol = LoginController(loginui, self)
        self.testcontrol = TestController(testui=self.mainui.testInterface, app=self)
        self.homecontrol = HomeController(homeui=self.mainui.homeInterface, app=self)
        self.loginui.close_signal.connect(self.closed)
        self.mainui.close_signal.connect(self.closed)
        self.closed.connect(self.close)

    def send_text_message(self, message):
        conf_client.send_message(message)

    def send_video_start(self, video_type='camera'):
        conf_client.start_video_sender(video_type)

    def send_video_stop(self):
        conf_client.stop_video_sender()

    def send_video_switch_mode(self):
        conf_client.switch_video_mode()

    def send_audio_start(self):
        conf_client.start_send_audio()

    def change_audio_volume(self, volume):
        # TODO
        pass

    def send_audio_stop(self):
        conf_client.stop_send_audio()

    def cancel_conference(self):
        conf_client.cancel_conference()

    def get_meetings(self):
        res = conf_client.get_conference_list()
        details = {}
        for conf_id in res['conferences']:
            for detail in res['conferences_detail']:
                if detail['conference_id'] == conf_id:
                    details[conf_id] = detail
        return res['conferences'], details

    def switch_ui(self, to='main'):
        if to == 'main':
            self.mainui.show()
            self.loginui.hide()
            try:
                self.homecontrol.meetingCardGroup.flush_meeting_cards()
                print("[INFO] Meeting cards flushed")
            except Exception as e:
                print("[ERROR] failed to flush meeting cards due to ", e)
        elif to == 'login':
            self.mainui.hide()
            self.loginui.show()
        else:
            print('Invalid UI name')

    def start(self):
        self.logincontol.register_all_action()

    def close(self):
        conf_client.logout()
        self.mainui.close()
        self.loginui.close()

    def on_app_close(self):
        """处理应用关闭时的逻辑"""
        # 清理资源
        print("Application is closing. Performing cleanup...")

        # 停止音频、视频等服务

        try:
            # 断开与服务器的连接
            self.send_audio_stop()
            self.send_video_stop()
        except Exception as e:
            print(f"Error disconnecting from server: {e}")
        finally:
            conf_client.logout()

class LoginController:
    def __init__(self, loginui: LoginWindow, app: AppController):
        self.loginui = loginui
        self.app = app
        self.isremember = True # load from config
        self.loadRemember()

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
        self.loginui.checkBox.stateChanged.connect(self.setRemember)

    def login(self):
        username = self.loginui.lineEdit_3.text()
        password = self.loginui.lineEdit_4.text()
        if not username or not password:
            # show error message
            self.loginui.info('error', 'Error', 'Username or password is empty')
            return
        # send login request to server
        server_response = conf_client.login(username, password)
        if server_response['status'] == Status.SUCCESS.value:
            self.loginui.info('success', 'Success', 'Login successfully')
            self.remember()
            self.switch_to_main()
            self.app.mainui.setNavigationName(username)
        else:
            self.loginui.info('error', 'Error', server_response['message'])

    def register(self):
        username = self.loginui.lineEdit_3.text()
        password = self.loginui.lineEdit_4.text()
        if not username or not password:
            # show error message
            self.loginui.info('error', 'Error', 'Username or password is empty')
            return
        # send register request to server
        # login automatically if register success
        register_res = conf_client.register(username, password)
        if register_res['status'] == Status.SUCCESS.value:
            self.loginui.info('success', 'Success', 'Register successfully')
            login_res = conf_client.login(username, password)
            if login_res['status'] == Status.SUCCESS.value:
                self.loginui.info('success', 'Success', 'Login successfully')
                self.remember()
                self.switch_to_main()
            else:
                self.loginui.info('error', 'Error', login_res['message'])
        else:
            self.loginui.info('error', 'Error', register_res['message'])

    def setRemember(self, state):
        self.isremember = state == 2

    def remember(self):
        if self.isremember:
            # save to config
            AppConfig.setUsernameCache(self.loginui.lineEdit_3.text())
            AppConfig.setPasswordCache(self.loginui.lineEdit_4.text())
            AppConfig.save()

    def loadRemember(self):
        self.loginui.lineEdit_3.setText(AppConfig.usernameCache())
        self.loginui.lineEdit_4.setText(AppConfig.passwordCache())

    def switch_to_main(self):
        # switch to main view
        self.app.switch_ui('main')
        pass

    def stop_thread(self):
        pass

class HomeController:

    def __init__(self, homeui: HomeInterface, app: AppController):
        self.interface = homeui
        self.app = app
        self.meetingCreateHandler = MeetingCreate(self.interface, self.app)
        self.meetingCardGroup = MeetingCardsGroupHandler(self.interface, self.app)
        self.meetingController = None
        self.meetingInterface = None

        # connect signal
        self.meetingCreateHandler.meeting_created.connect(self.handle_meeting_create)
        self.meetingCardGroup.meeting_joined.connect(self.handle_meeting_join)

    def handle_meeting_create(self, meeting_data):

        try:
            response = conf_client.create_conference(meeting_data['meeting_name'])
            if response['status'] == Status.SUCCESS.value:
                # self.interface.info('success', 'Success', 'Meeting created successfully')
                self.meetingInterface = MeetingInterfaceBase()
                self.meetingInterface.setTitle(meeting_data['meeting_name'])

                user_view = conf_client.user()
                self.meetingController = MeetingController(self.meetingInterface, self.app, user_view, isOwned=True)
                self._init_signal_connection()
                self.app.mainui.hide()
                self.meetingInterface.show()
            else:
                self.interface.info('error', 'Error', response['message'])

        except Exception as e:
            print(e)
            # self.interface.info('error', 'Error', 'Failed to create meeting')
            return

    def _init_signal_connection(self):
        if self.meetingController:
            self.meetingController.closed.connect(self.handle_quit)
            self.app.message_received.connect(self.meetingController.message_received)
            self.app.video_received.connect(self.meetingController.video_received)
            self.app.control_received.connect(self.meetingController.control_received)
            self.app.control_received.connect(self.handle_meeting_close)

    def handle_meeting_join(self, meeting_id, meeting_name):
        try:
            response = conf_client.join_conference(meeting_id)
            if response['status'] == Status.SUCCESS.value:
                self.meetingInterface = SimpleMeetingInterface()
                self.meetingInterface.setTitle(meeting_name)
                user_view = conf_client.user()
                self.meetingController = MeetingController(self.meetingInterface, self.app, user_view, isOwned=False)
                self._init_signal_connection()
                self.app.mainui.hide()
                self.meetingInterface.show()
            else:
                self.interface.info('error', 'Error', response['message'])
        except Exception as e:
            print(e)
            self.interface.info('error', 'Error', 'Failed to join meeting')

    def handle_meeting_close(self, message_type: MessageType, _):
        if message_type == MessageType.QUIT:
            self.app.mainui.show()
            if self.meetingInterface:
                self.meetingInterface.deleteLater()
            self.meetingInterface = None
            self.meetingController = None

    def handle_quit(self):
        try:
            conf_client.quit_conference()
        except Exception as e:
            print(e)

class TestController:

    def __init__(self, testui: TestInterface, app: AppController):
        self.interface = testui
        self.app = app
        self.video_preview = VideoPreview(self.interface.previewarea)
        self.audio_preview = AudioPreview(self.interface.soundpreviewarea)

## Exception handling
def excepthook(exc_type, exc_value, exc_tb):
    message = f"An exception of type {exc_type.__name__} occurred.\n" \
                f"Exception message: {str(exc_value)}\n" \
                f"Traceback: {exc_tb}"
    print(message)
    try:
        conf_client.logout()
    except Exception as e:
        print(f"Error disconnecting from server: {e}")
    sys.__excepthook__(exc_type, exc_value, exc_tb)

from PyQt5.QtCore import Qt, QLocale
from PyQt5.QtWidgets import QApplication, QMessageBox
from qfluentwidgets import FluentTranslator

if __name__ == '__main__':
    sys.excepthook = excepthook
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
    conf_client.set_controller(controller)
    controller.start()

    atexit.register(controller.on_app_close)
    sys.exit(app.exec_())

