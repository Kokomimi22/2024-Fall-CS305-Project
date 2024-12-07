import json
import socket
import threading
from enum import Enum

from common.user import User
from util import *


class ConferenceClient:
    def __init__(self, ):
        # sync client
        self.userInfo: User = None
        self.recv_thread = None
        self.is_working = True
        self.conf_server_addr = None  # conference server addr
        self.data_server_addr: Dict[str, Any] = None  # data server in the conference server
        self.on_meeting = False  # status
        self.conns: socket.socket = None  # you may need to maintain multiple conns for a single conference
        self.support_data_types = ['screen', 'camera', 'audio']  # the data types that can be shared, which should be modified
        self.share_data = {}
        self.sharing_task = None

        self.conference_info = None  # you may need to save and update some conference_info regularly
        self.conference_id = None  # conference_id for distinguish difference conference
        self.recv_data = None  # you may need to save received streamd data from other clients in conference

        self.update_handler = {} # {data_type: handler} for GUI update

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
            else:
                print(f"[Error]: {response['message']}")
            return response

    def create_conference(self):
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
                'client_id': self.userInfo.uuid
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
                self.data_server_addr = {dataType: (SERVER_IP, port) for dataType, port in recv_data['data_serve_ports'].items()}
                self.on_meeting = True
                self.start_conference()
                print(f'[Info]: Joined conference {conference_id} successfully')
            else:
                print(f'[Error]: Failed to join conference {conference_id}')
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
        self.conns.sendall(json.dumps(quit_request).encode())

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
            'client_name': self.userInfo.username,
            'message': message
        }
        self.conns.sendall(json.dumps(message_post).encode())

    def keep_share(self, data_type, send_conn, capture_function, compress=None, fps_or_frequency=30):
        """
        running task: keep sharing (capture and send) certain type of data from server or clients (P2P)
        you can create different functions for sharing various kinds of data
        """
        while self.on_meeting:
            if data_type == 'screen':
                screen_shot = capture_function()
                send_conn.send(b'screen')
                send_conn.sendall(compress(screen_shot) if compress else screen_shot)
                send_conn.send(b'eof')
                time.sleep(1 / fps_or_frequency)
            elif data_type == 'camera':
                camera_frame = capture_function()
                send_conn.send(b'camera')
                send_conn.sendall(compress(camera_frame) if compress else camera_frame)
                send_conn.send(b'eof')
                time.sleep(1 / fps_or_frequency)
            elif data_type == 'audio':
                audio_data = capture_function()
                send_conn.send(b'audio')
                send_conn.sendall(audio_data)
                send_conn.send(b'eof')
                time.sleep(1 / fps_or_frequency)

    def share_switch(self, data_type):
        """
        switch for sharing certain type of data (screen, camera, audio, etc.)
        """
        self.conns.sendall(f'share {data_type}'.encode('utf-8'))

        # test keep_share
        _sharing_task = None
        if data_type == 'screen':
            _sharing_task = threading.Thread(target=self.keep_share,
                                             args=(data_type, self.conns, capture_screen, compress_image))
        elif data_type == 'camera':
            _sharing_task = threading.Thread(target=self.keep_share,
                                             args=(data_type, self.conns, capture_camera, compress_image))
        elif data_type == 'audio':
            _sharing_task = threading.Thread(target=self.keep_share, args=(data_type, self.conns, capture_voice))
        self.sharing_task = _sharing_task
        _sharing_task.start()

    def keep_recv(self, recv_conn=None, data_type=None, decompress=None):
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
                        if message['type'] == MessageType.TEXT_MESSAGE.value and self.update_handler.get('text'):
                            self.update_handler['text'](message)
                            print(f'{message["client_name"]}: {message["message"]}')
                    except UnicodeDecodeError:
                        print(f'[Info]: Received data: {len(_recv_data)} bytes')


        self.recv_thread = threading.Thread(target=recv_task)
        self.recv_thread.start()

    def output_data(self):
        """
        running task: output received stream data
        """
        # write is into a file
        print(f'[Info]: Received data: {self.recv_data}')

    def save_img(self, img_data, img_path):
        """
        save image data to a file
        :param img_data: bytes, image data
        :param img_path: str, image file path
        """
        with open(img_path, 'wb') as f:
            f.write(img_data)

    def start_conference(self):
        """
        init conns when create or join a conference with necessary conference_info
        and
        start necessary running task for conference
        """
        self.conns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conns.connect(self.conf_server_addr)
        init_request = {
            'type': MessageType.INIT.value,
            'client_id': self.userInfo.uuid
        }
        self.conns.sendall(json.dumps(init_request).encode())
        self.keep_recv(recv_conn=self.conns, data_type='screen', decompress=None)

    def close_conference(self):
        """
        close all conns to servers or other clients and cancel the running tasks
        pay attention to the exception handling
        """
        self.on_meeting = False
        if self.conns:
            try:
                self.conns.shutdown(socket.SHUT_RDWR)
            except socket.error as e:
                print(f"[Error]: Error shutting down connection: {e}")
            finally:
                try:
                    self.conns.close()
                    print("[Info]: Connection closed successfully.")
                except socket.error as e:
                    print(f"[Error]: Error closing connection: {e}")
            self.conns = None

    def start(self):
        """
        execute functions based on the command line input
        """
        while True:
            if not self.on_meeting:
                status = 'Free'
            else:
                status = f'OnMeeting-{self.conference_id}'

            cmd_input = input(f'({status}) Please enter a operation (enter "?" to help): ')
            self.command_parser(cmd_input)

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
            message = json.dumps({'type': MessageType.LOGOUT.value, 'uuid': self.userInfo.uuid})
            s.sendall(message.encode())
            recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
            response = json.loads(recv_data)
            if response.get('status') == Status.SUCCESS.value:
                print('[Info]: Logged out successfully')
                self.userInfo = None
            else:
                print(f"[Error]: {response['message']}")
            return response

    def command_parser(self, cmd_input):
        """
            parse the command line input and execute the corresponding functions
            """
        cmd_input = cmd_input.strip().lower().strip()
        fields = cmd_input.split(maxsplit=2)
        if not fields:
            return
        if fields[0] in ('create', 'join', 'quit', 'cancel') and self.userInfo is None:
            print('[Error]: Please login first')
            return
        if len(fields) == 1:
            if cmd_input in ('?', '？'):
                print(HELP)
            elif cmd_input == 'create':
                self.create_conference()
            elif cmd_input == 'quit':
                self.quit_conference()
            elif cmd_input == 'cancel':
                self.cancel_conference()
            elif cmd_input == 'exit':
                if self.on_meeting:
                    self.logout()
                    self.quit_conference()
            else:
                print('[Error]: Invalid command' + '\r\n' + HELP)
        elif len(fields) == 2:
            arg = fields[1]
            if fields[0] == 'join' and arg.isdigit():
                self.join_conference(int(arg))
            elif fields[0] == 'switch' and arg in self.support_data_types:
                self.share_switch(arg)
            elif fields[0] == 'share':
                self.share_switch(arg)
            else:
                print('[Error]: Invalid command' + '\r\n' + HELP)
        elif len(fields) == 3:
            arg1, arg2 = fields[1], fields[2]
            if fields[0] == 'register':
                self.register(arg1, arg2)
            elif fields[0] == 'login':
                self.login(arg1, arg2)
            else:
                print('[Error]: Invalid command' + '\r\n' + HELP)
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER_IP, MAIN_SERVER_PORT))
                s.sendall(cmd_input.encode())
                self.recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
                print(f'[Info]: {self.recv_data}')

if __name__ == '__main__':
    client1 = ConferenceClient()
    client1.start()
