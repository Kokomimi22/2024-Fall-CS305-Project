import json
import threading
import time

from DataTransfer.Video.Camera import Camera
from DataTransfer.Video.VideoReceiver import VideoReceiver
from DataTransfer.Video.VideoSender import VideoSender
from common.user import User
from util import *


class ConferenceClient:
    def __init__(self, app=None):
        # sync client
        self.userInfo: User = None
        self.recv_thread: Dict[str, threading.Thread] = {}
        self.send_thread: Dict[str, threading.Thread] = {}
        self.is_working = True
        self.conf_server_addr = None  # conference server addr
        self.data_server_addr: Dict[str, Any] = None  # data server in the conference server
        self.on_meeting = False  # status
        self.conns: Dict[str, socket.socket] = {}  # you may need to maintain multiple conns for a single conference
        self.support_data_types = ['screen', 'camera', 'audio',
                                   'text']  # the data types that can be shared, which should be modified
        self.share_data = {}
        self.sharing_task = None
        self.conference_info = None  # you may need to save and update some conference_info regularly
        self.conference_id = None  # conference_id for distinguish difference conference
        self.recv_data = None  # you may need to save received streamd data from other clients in conference
        self.videoSender: VideoSender = None  # you may need to maintain multiple video senders for a single conference
        self.videoReceiver: VideoReceiver = None
        self.update_signal = None

    def user(self):
        return self.userInfo

    def isWorking(self):
        return self.is_working

    def hasOnMeeting(self):
        return self.on_meeting

    @staticmethod
    def get_conference_list():
        """
        get all available conferences from the server
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            message = json.dumps({'type': MessageType.GET_CONFERENCES.value})
            s.sendall(message.encode())
            recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
            response = json.loads(recv_data)
            if response['status'] == Status.SUCCESS.value:
                print(response['conferences'])
                print(response)
            else:
                print(f"[Error]: {response['message']}")
            return response

    def create_conference(self, conference_name: str):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        """
        if self.on_meeting:
            print(f'[Error]: You are already in a conference {self.conference_id}')
            return f'[Error]: You are already in a conference {self.conference_id}'

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            create_request = {
                'type': MessageType.CREATE.value,
                'client_id': self.userInfo.uuid,
                'conference_name': conference_name
            }
            s.sendall(json.dumps(create_request).encode())
            recv_data: Dict[str, Any] = json.loads(s.recv(CONTROL_LINE_BUFFER).decode('utf-8'))
            if recv_data['status'] == Status.SUCCESS.value:
                #成功了就加入会议
                self.join_conference(recv_data['conference_id'])
                print(f'[Info]: Created conference {self.conference_id} successfully')
            else:
                print(f'[Error]: {recv_data["message"]}')
            return recv_data

    def join_conference(self, conference_id: int):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        if self.on_meeting:
            print(f'[Error]: You are already in a conference {self.conference_id}')
            return
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            join_request = {
                'type': MessageType.JOIN.value,
                'client_id': self.userInfo.uuid,
                'conference_id': conference_id
            }
            s.sendall(json.dumps(join_request).encode())
            recv_data = json.loads(s.recv(CONTROL_LINE_BUFFER).decode('utf-8'))
            if recv_data['status'] == Status.SUCCESS.value:
                self.conference_id = conference_id
                # 记录会议服务器和数据服务器的端口号，以便之后传输数据使用
                self.conf_server_addr = (SERVER_IP, recv_data['conference_serve_port'])
                self.data_server_addr = {dataType: (SERVER_IP, port) for dataType, port in
                                         recv_data['data_serve_ports'].items()}
                self.on_meeting = True
                self.start_conference()
                print(f'[Info]: Joined conference {conference_id} successfully')
            else:
                print(f'[Error]: {recv_data["message"]}')
            return recv_data

    def quit_conference(self):
        """
        quit your on-going conference
        """
        if not self.on_meeting:
            print(f'[Error]: You are not in a conference')
            return
        quit_request = {
            'type': MessageType.QUIT.value,
            'client_id': self.userInfo.uuid,
        }
        self.conns['text'].sendall(json.dumps(quit_request).encode())

    def cancel_conference(self):
        """
        cancel your on-going conference (when you are the conference manager): ask server to close all clients
        """
        if not self.on_meeting:
            print(f'[Error]: You are not in a conference')
            return
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            cancel_request = {
                'type': MessageType.CANCEL.value,
                'client_id': self.userInfo.uuid,
                'conference_id': self.conference_id
            }
            s.sendall(json.dumps(cancel_request).encode())
            recv_data = json.loads(s.recv(CONTROL_LINE_BUFFER).decode('utf-8'))
            if recv_data['status'] == Status.SUCCESS.value:
                self.on_meeting = False
            else:
                print(f'[Error]: {recv_data["message"]}')
            return recv_data

    def send_message(self, message):
        """
        send message to other clients in the conference
        """
        if not self.on_meeting:
            print(f'[Error]: You are not in a conference')
            return
        message_post = {
            'type': MessageType.TEXT_MESSAGE.value,
            'sender_name': self.userInfo.username,
            'message': message
        }
        self.conns['text'].sendall(json.dumps(message_post).encode())

    def keep_recv_text(self, recv_conn: socket.socket = None):
        """
        running task: keep receiving certain type of data (save or output)
        you can create other functions for receiving various kinds of data
        """

        def recv_task():
            while self.on_meeting:
                _recv_data = recv_conn.recv(DATA_LINE_BUFFER)
                if _recv_data == b'Quitted' or _recv_data == b'Cancelled':
                    print(f'You have been quitted from the conference {self.conference_id}')
                    self.close_conference()
                    break
                if _recv_data:
                    try:
                        message = json.loads(_recv_data.decode())
                        if message['type'] == MessageType.TEXT_MESSAGE.value and self.update_signal.get('text'):
                            self.update_signal['text'].emit(message['sender_name'], message['message'])
                            print(f'{message["sender_name"]}: {message["message"]}')
                    except UnicodeDecodeError:
                        print(f'[Info]: Received data: {len(_recv_data)} bytes')

        self.recv_thread['text'] = threading.Thread(target=recv_task)
        self.recv_thread['text'].start()

    def keep_recv_video(self):

        def recv_task():
            while self.on_meeting:
                _recv_data = self.videoReceiver.output_image()
                if _recv_data:
                    self.update_signal['video'].emit(_recv_data)
                time.sleep(0.01)

        self.recv_thread['video'] = threading.Thread(target=recv_task)
        self.recv_thread['video'].start()

    def output_data(self):
        """
        running task: output received stream data
        """
        # write is into a file
        print(f'[Info]: Received data: {self.recv_data}')

    def start_conference(self):
        """
        init conns when create or join a conference with necessary conference_info
        and
        start necessary running task for conference
        """
        self.conns['text'] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conns['camera'] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.conns['text'].connect(self.conf_server_addr)
        self.conns['camera'].connect(self.data_server_addr['camera'])
        init_request = {
            'type': MessageType.INIT.value,
            'client_id': self.userInfo.uuid
        }
        # Establish connection with text data server
        self.conns['text'].sendall(json.dumps(init_request).encode())
        # start receiving text data
        self.keep_recv_text(self.conns['text'])
        # Establish connection with video data server
        self.conns['camera'].sendall(json.dumps(init_request).encode())
        self.videoReceiver = VideoReceiver(self.conns['camera'])
        self.keep_recv_video()
        # start receiving video data
        self.recv_thread['camera'] = threading.Thread(target=self.videoReceiver.start)
        self.recv_thread['camera'].start()

    def close_conference(self):
        """
        close all conns to servers or other clients and cancel the running tasks
        pay attention to the exception handling
        """
        self.on_meeting = False
        if self.conns:
            try:
                if self.videoSender:
                    self.videoSender.terminate()
                for recv_thread in self.recv_thread.values():
                    if recv_thread is not threading.current_thread():
                        recv_thread.join()
                if self.videoReceiver:
                    self.videoReceiver.terminate()
                for send_thread in self.send_thread.values():
                    if send_thread is not threading.current_thread():
                        send_thread.join()
                for conn in self.conns.values():
                    conn.shutdown(socket.SHUT_RDWR)
            except socket.error as e:
                print(f"[Error]: Error shutting down connection: {e}")
            finally:
                try:
                    for conn in self.conns.values():
                        conn.close()
                    print("[Info]: Connection closed successfully.")
                except socket.error as e:
                    print(f"[Error]: Error closing connection: {e}")

    def start_video_sender(self):
        """
        start video sender for sharing camera data
        """
        if not self.on_meeting:
            print(f'[Error]: You are not in a conference')
            return
        if not self.videoSender:
            camera = Camera()
            self.videoSender = VideoSender(camera, self.conns['camera'], self.userInfo.uuid)
        self.send_thread['camera'] = threading.Thread(target=self.videoSender.start)
        self.send_thread['camera'].start()

    def stop_video_sender(self):
        """
        stop video sender for sharing camera data
        """
        if self.videoSender:
            self.videoSender.terminate()
            self.videoSender = None
            self.send_thread['camera'].join()
        else:
            print(f'[Error]: Video sender is not started')

    def register(self, username, password):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            message = json.dumps({'type': MessageType.REGISTER.value, 'username': username, 'password': password})
            s.sendall(message.encode())
            recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
            response = json.loads(recv_data)
            if response['status'] == Status.SUCCESS.value:
                print('Register successfully')
            else:
                print(f"[Error]: {response['message']}")
            return response

    def login(self, username, password):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            message = json.dumps({'type': MessageType.LOGIN.value, 'username': username, 'password': password})
            s.sendall(message.encode())
            recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
            response = json.loads(recv_data)
            if response['status'] == Status.SUCCESS.value:
                print('Login successfully')
                uuid = response['uuid']
                self.userInfo = User(uuid, username, password)
            else:
                print(f"[Error]: {response['message']}")
            return response

    def logout(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            message = json.dumps({'type': MessageType.LOGOUT.value, 'client_id': self.userInfo.uuid})
            s.sendall(message.encode())
            recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
            response = json.loads(recv_data)
            if response.get('status') == Status.SUCCESS.value:
                print('[Info]: Logged out successfully')
                self.userInfo = None
            else:
                print(f"[Error]: {response['message']}")
            return response

    def set_controller(self, app):
        self.update_signal = {
            'text': app.message_received,  # type: pyqtSignal(str, str)
            'video': app.video_received,  # type: pyqtSignal(Image)
            'audio': app.audio_received  # type: pyqtSignal(bytes)
        }  # {data_type: handler} for GUI update


