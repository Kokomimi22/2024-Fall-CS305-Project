import json
import threading
import time

from PyQt5.QtCore import pyqtSignal

from DataTransfer.Audio.AudioReceiver import AudioReceiver
from DataTransfer.Audio.AudioSender import AudioSender
from DataTransfer.Video.Camera import Camera
from DataTransfer.Video.VideoReceiver import VideoReceiver
from DataTransfer.Video.VideoSender import VideoSender
from common.user import User
from util import *


class ConferenceClient:
    def __init__(self):
        # sync client
        self.userInfo: User = None
        self.recv_thread: Dict[str, threading.Thread] = {}
        self.send_thread: Dict[str, threading.Thread] = {}
        self.is_working = True
        self.conf_server_addr = None  # conference server addr
        self.data_server_addr: Dict[str, Any] = None  # data server in the conference server
        self.on_meeting = False  # status
        self.isManager = False  # whether the client is the manager of the conference
        self.conns: Dict[str, socket.socket] = {}  # connections for different data types and **p2p**
        self.support_data_types = \
            ['video', 'audio', 'text']  # the data types that can be shared, which should be modified
        self.conference_id = None  # conference_id for distinguish difference conference
        self.recv_data = None  # you may need to save received streamd data from other clients in conference
        self.videoSender: VideoSender = None  # you may need to maintain multiple video senders for a single conference
        self.videoReceiver: VideoReceiver = None
        self.audioSender: AudioSender = None
        self.audioReceiver: AudioReceiver = None
        self.update_signal = {dataType: None for dataType in self.support_data_types}  # signal for updating GUI
        self.is_p2p = False  # whether the client is in P2P mode
        self.p2p_addr = {}  # for p2p connection bind
        self.switch_distribution_mode_lock = threading.Lock()

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
                # 成功了就加入会议
                self.join_conference(recv_data['conference_id'])
                self.isManager = True
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
            return f'[Error]: You are already in a conference {self.conference_id}'
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
        quit your ongoing conference
        """
        if not self.on_meeting:
            print(f'[Error]: You are not in a conference')
            return f'[Error]: You are not in a conference'
        if self.isManager:
            return self.cancel_conference()
        quit_request = {
            'type': MessageType.QUIT.value,
            'client_id': self.userInfo.uuid,
        }
        self.conns['text'].sendall(json.dumps(quit_request).encode())

    def cancel_conference(self):
        """
        cancel your ongoing conference (when you are the conference manager): ask server to close all clients
        """
        if not self.on_meeting:
            print(f'[Error]: You are not in a conference')
            return f'[Error]: You are not in a conference'
        if not self.isManager:
            print(f'[Error]: You are not the manager of this conference')
            return f'[Error]: You are not the manager of this conference'
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
                self.isManager = False
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
        connection = self.conns['p2p'] if self.is_p2p else self.conns['text']
        connection.sendall(json.dumps(message_post).encode())

    def recv_conference_task(self):
        """处理普通会议消息的接收任务"""
        while self.on_meeting:
            try:
                _recv_data = self.conns['text'].recv(DATA_LINE_BUFFER)
            except ConnectionResetError:
                print(f'[Info]: Server disconnected')
                break
            # 检查是否退出会议
            if not _recv_data or _recv_data == b'Quitted' or _recv_data == b'Cancelled':
                if self.update_signal.get('control'):
                    self.update_signal['control'].emit(MessageType.QUIT, '')
                print(f'You have been quitted from the conference {self.conference_id}')
                self.close_conference()
                break

            # 解析和处理消息
            try:
                message = json.loads(_recv_data.decode())

                if message['type'] == MessageType.TEXT_MESSAGE.value:
                    if self.update_signal.get('text'):
                        self.update_signal['text'].emit(message['sender_name'], message['message'])
                    print(f'{message["sender_name"]}: {message["message"]}')

                elif message['type'] == MessageType.SWITCH_TO_P2P.value:
                    self.conns['p2p'] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.conns['p2p'].bind(('0.0.0.0', 0))
                    self.conns['text'].sendall(
                        json.dumps({
                            'type': MessageType.P2P_INFOS_NOTIFICATION.value,
                            'client_id': self.userInfo.uuid,
                            'p2p_info': self.conns['p2p'].getsockname()[1]
                        }).encode())

                elif message['type'] == MessageType.P2P_INFOS_NOTIFICATION.value:
                    self.p2p_addr = {key: tuple(value) for key, value in message['peer_addr'].items()}
                    self._switch_to_p2p()
                    print(f'[Info]: Switch to P2P mode')

                elif message['type'] == MessageType.SWITCH_TO_CS.value:
                    # 仅当当前为P2P模式时才切换
                    if not self.is_p2p:
                        continue
                    self._switch_to_cs()
                    self.p2p_addr = {}
                    if 'p2p' in self.conns:
                        try:
                            self.conns['p2p'].shutdown(socket.SHUT_RDWR)
                            self.conns['p2p'].close()
                        except socket.error as e:
                            print(f"[Error]: Error closing connection: {e}")
                    self.conns.pop('p2p', None)
                    print(f'[Info]: Switch to CS mode')

                else:
                    print(f'[Error]: Received unknown data: {message}')

            except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
                print(f'[Info]: Received Unknown data: {len(_recv_data)} bytes')

    def recv_p2p_task(self):
        """处理P2P消息的接收任务"""
        # 设置为非阻塞模式, 避免卡死
        self.conns['p2p'].setblocking(False)
        while self.on_meeting and self.is_p2p:
            try:
                _recv_data = self.conns['p2p'].recv(DATA_LINE_BUFFER)
            except BlockingIOError:
                continue
            except ConnectionResetError:
                print(f'[Info]: Peer disconnected')
                break
            if not _recv_data:
                break
            # 解析和处理消息
            try:
                message = json.loads(_recv_data.decode())

                if message['type'] == MessageType.TEXT_MESSAGE.value:
                    if self.update_signal.get('text'):
                        self.update_signal['text'].emit(message['sender_name'], message['message'])
                    print(f'{message["sender_name"]}: {message["message"]}')

                else:
                    print(f'[Error]: Received unknown data: {message}')

            except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
                print(f'[Info]: Received Unknown data: {len(_recv_data)} bytes')

    def output_data(self):
        """
        running task: output received stream data
        """
        print(f'[Info]: Received data: {self.recv_data}')

    def reconnect(self, addr_dict: Dict[str, Tuple[str, int]]):
        """
        reconnect to the server or other clients
        """
        print(f'[Info]: Reconnecting to {"server" if not self.is_p2p else "peer"} {addr_dict}')
        if self.is_p2p:
            while True:
                try:
                    self.conns['p2p'].connect(addr_dict['text'])
                    break
                except ConnectionRefusedError:
                    print(f'[Info]: Waiting for the peer to connect')
                    time.sleep(1)
            self.recv_thread['p2p_text'] = threading.Thread(target=self.recv_p2p_task)
            self.recv_thread['p2p_text'].start()
        elif 'p2p_text' in self.recv_thread:
            self.recv_thread['p2p_text'].join()
            self.recv_thread.pop('p2p_text', None)
        if self.videoSender:
            self.videoSender.reconnect(addr_dict['video'])
        if self.audioSender:
            self.audioSender.reconnect(addr_dict['audio'])

    def _switch_to_p2p(self):
        """
        Switch to p2p mode
        """
        with self.switch_distribution_mode_lock:
            self.is_p2p = True
            self.reconnect(self.p2p_addr)

    def _switch_to_cs(self):
        """
        Switch to client-server mode
        """
        with self.switch_distribution_mode_lock:
            self.is_p2p = False
            self.reconnect(self.data_server_addr)

    def _init_connections(self, addr_dict: Dict[str, Tuple[str, int]]):
        """
        Initialize connections for conference mode
        :param addr_dict: dict of addresses for different data types
        """
        connections = self.conns
        # Initialize sockets
        for medium in ['text', 'video', 'audio']:
            sock_type = socket.SOCK_STREAM if medium == 'text' else socket.SOCK_DGRAM
            connections[medium] = socket.socket(socket.AF_INET, sock_type)
            if medium != 'video':
                connections[medium].connect(addr_dict[medium])

    def start_sender_and_receiver(self):
        """
        Start video and audio senders and receivers.
        and bind the connections to the server or other clients.
        :return:
        """
        connections = self.conns
        # Initialize text connection
        self.recv_thread['text'] = threading.Thread(target=self.recv_conference_task)
        # Set the thread as daemon so that it will be terminated when the main thread exits
        self.recv_thread['text'].daemon = True
        self.recv_thread['text'].start()

        # Initialize video connection
        self.videoReceiver = VideoReceiver(connections['video'], self.update_signal['video'])
        self.videoSender = VideoSender(None, connections['video'], self.userInfo.uuid, self.data_server_addr['video'])
        self.videoReceiver.start()

        # Initialize audio connection
        self.audioReceiver = AudioReceiver(connections['audio'], streamout)
        self.audioSender = AudioSender(connections['audio'], self.userInfo.uuid, streamin)
        self.audioReceiver.start()
        self.audioSender.start()

    def start_conference(self):
        """
        Initialize connections and start conference
        """
        with self.switch_distribution_mode_lock:
            addr_dict = {
                'text': self.conf_server_addr,
                'video': self.data_server_addr['video'],
                'audio': self.data_server_addr['audio']
            }

            self._init_connections(addr_dict)
            # Send init request to servers
            init_request = {
                'type': MessageType.INIT.value,
                'client_id': self.userInfo.uuid
            }

            for medium in ['text', 'video', 'audio']:
                if medium == 'video':
                    self.conns[medium].sendto(json.dumps(init_request).encode(), addr_dict[medium])
                    continue
                self.conns[medium].sendall(json.dumps(init_request).encode())

            self.start_sender_and_receiver()

    def close_conference(self):
        """
        close all conns to servers or other clients and cancel the running tasks
        pay attention to the exception handling
        """
        self.on_meeting = False
        if self.conns:
            try:
                # Terminate video and audio senders/receivers if they exist
                for attr in ['videoSender', 'videoReceiver', 'audioSender', 'audioReceiver']:
                    instance = getattr(self, attr, None)
                    if instance:
                        instance.terminate()
                        setattr(self, attr, None)
                self.is_p2p = False
                self.isManager = False
                # Join send and receive threads if they are not the current thread
                for thread_dict in [self.send_thread, self.recv_thread]:
                    for thread in thread_dict.values():
                        if thread is not threading.current_thread():
                            thread.join()
                for datatype, conn in self.conns.items():
                    if conn and (datatype not in ['video', 'audio']):
                        conn.shutdown(socket.SHUT_RDWR)
            except socket.error as e:
                print(f"[Error]: Error shutting down connection: {e}")
            finally:
                try:
                    for conn in self.conns.values():
                        if conn:
                            conn.close()
                    self.conns.clear()
                    self.p2p_addr.clear()
                    self.send_thread.clear()
                    self.recv_thread.clear()
                    print("[Info]: Connection closed successfully.")
                except socket.error as e:
                    print(f"[Error]: Error closing connection: {e}")

    def switch_video_mode(self):
        """
        switch video mode between camera and screen
        """
        if not self.on_meeting or not self.videoSender:
            print(f'[Error]: You are not in a conference')
            return
        if not self.videoSender.isRunning():
            print(f'[Error]: Video sender is not started')
            return
        self.videoSender.switch_mode()

    def start_video_sender(self, mode='camera'):
        """
        start video sender for sharing camera data
        """
        if not self.on_meeting or not self.videoSender:
            print(f'[Error]: You are not in a conference')
            return
        if self.videoSender.isRunning():
            print(f'[Error]: Video sender is already started. ' +
                  'I guess you want to switch video mode, please use "switch_video_mode" command')
            return
        camera = Camera(mode)
        self.videoSender.camera = camera
        print(f'[Info]: Start video sender in {mode} mode')
        self.videoSender.start()

    def stop_video_sender(self):
        """
        stop video sender for sharing camera data
        """
        if self.videoSender and self.videoSender.isRunning():
            self.videoSender.stop_video_send()
            print(f'[Info]: Stop video sender')
        else:
            print(f'[Error]: Video sender is not started')

    def start_send_audio(self):
        """
        start audio sender for sharing audio data
        """
        if not self.on_meeting:
            print(f'[Error]: You are not in a conference')
            return
        if self.audioSender:
            self.audioSender.sending = True
            print(f'[Info]: Start sending audio')

    def stop_send_audio(self):
        """
        stop audio sender for sharing audio data
        """
        if not self.on_meeting:
            print(f'[Error]: You are not in a conference')
            return
        if self.audioSender:
            self.audioSender.sending = False
            print(f'[Info]: Stop sending audio')

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
        if not self.userInfo:
            print(f'[Error]: You are not logged in')
            return
        if self.on_meeting:
            self.quit_conference()
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
            'control': app.control_received  # type: pyqtSignal(MessageType, str)
        }  # {data_type: handler} for GUI update
