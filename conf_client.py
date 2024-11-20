import socket
import threading

from user import User
from config import *
from util import *


class ConferenceClient:
    def __init__(self,):
        # sync client
        self.userInfo = None
        self.recv_thread = None
        self.is_working = True
        self.server_addr = None  # server addr
        self.on_meeting = False  # status
        self.conns = None  # you may need to maintain multiple conns for a single conference
        self.support_data_types = ['screen', 'camera', 'audio']  # the data types that can be shared, which should be modified
        self.share_data = {}
        self.sharing_task = None

        self.conference_info = None  # you may need to save and update some conference_info regularly
        self.conference_id = None  # conference_id for distinguish difference conference
        self.recv_data = None  # you may need to save received streamd data from other clients in conference

    def create_conference(self):
        """
        create a conference: send create-conference request to server and obtain necessary data to
        """
        if self.on_meeting:
            print(f'[Error]: You are already in a conference {self.conference_id}')
            return
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            s.sendall(f'create with {self.userInfo.uuid}'.encode())
            self.recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
            if self.recv_data.startswith('Created'):
                conference_id = self.recv_data.split(' ')[1]
                print(f'[Info]: Created conference {conference_id}')
                self.join_conference(conference_id=conference_id)
            else:
                print(f'[Error]: Failed to create conference')

    def join_conference(self, conference_id):
        """
        join a conference: send join-conference request with given conference_id, and obtain necessary data to
        """
        if self.on_meeting:
            print(f'[Error]: You are already in a conference {self.conference_id}')
            return
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            s.sendall(f'join {conference_id}'.encode())
            self.recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
            if self.recv_data.startswith('Joined'):
                print(f'[Info]: Joined conference {conference_id}')
                self.conference_id = conference_id
                conference_ports = self.recv_data.split(' ')[-1]
                self.server_addr = (SERVER_IP, int(conference_ports))
                self.on_meeting = True
                # start necessary running task for conference
                self.start_conference()
            else:
                print(f'[Error]: Failed to join conference {conference_id}')
    def quit_conference(self):
        """
        quit your on-going conference
        """
        self.conns.sendall(b'quit')

    def cancel_conference(self):
        """
        cancel your on-going conference (when you are the conference manager): ask server to close all clients
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            s.sendall(f'cancel {self.conference_id} with {self.userInfo.uuid}'.encode())
            self.recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
            if self.recv_data.startswith('Cancelled'):
                print(f'[Info]: Cancelled conference {self.conference_id}')
            else:
                print(f'[Error]: Failed to cancel conference {self.conference_id}')

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
        pass

    def share_switch(self, data_type):
        """
        switch for sharing certain type of data (screen, camera, audio, etc.)
        """
        self.conns.sendall(f'share {data_type}'.encode('utf-8'))

        # cmd_input = input(f'Please transfer the data: ').strip().lower()
        # while True:
        #     self.conns.sendall(cmd_input.encode('utf-8'))
        #     cmd_input = input(f'Is that over? ').strip().lower()
        #     if cmd_input == 'yes':
        #         self.conns.sendall(b'end')
        #         break

        # test keep_share
        if data_type == 'screen':
            _sharing_task = threading.Thread(target=self.keep_share, args=(data_type, self.conns, capture_screen, compress_image))
        elif data_type == 'camera':
            _sharing_task = threading.Thread(target=self.keep_share, args=(data_type, self.conns, capture_camera, compress_image))
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
                    print(f'The conference {self.conference_id} has been ended.')
                    self.close_conference()
                    break
                if _recv_data:
                    self.recv_data = _recv_data # bytes concatenation
                    self.output_data()

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
        self.conns.connect(self.server_addr)
        self.conns.sendall(f'init {self.userInfo.uuid}'.encode())
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
        while self.is_working:
            if not self.on_meeting:
                status = 'Free'
            else:
                status = f'OnMeeting-{self.conference_id}'

            recognized = True
            cmd_input = input(f'({status}) Please enter a operation (enter "?" to help): ').strip().lower()
            self.is_working = self.command_parser(cmd_input)
    def register(self, username, password):
        """
        register a new user
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            s.sendall(f'register {username} {password}'.encode())
            self.recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
            if self.recv_data.startswith('Registered'):
                print(f'[Info]: Registered successfully')
            else:
                print(f'[Error]: Failed to register')
    def login(self, username, password):
        """
        login with username and password
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, MAIN_SERVER_PORT))
            s.sendall(f'login {username} {password}'.encode())
            self.recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
            if self.recv_data.startswith('Logged'):
                print(f'[Info]: Logged in successfully')
                uuid = self.recv_data.split(' ')[-1]
                self.userInfo = User(uuid, username, password)
            else:
                print(f'[Error]: Failed to login')
    def command_parser(self, cmd_input):
            """
            parse the command line input and execute the corresponding functions
            """
            cmd_input = cmd_input.strip().lower().strip()
            fields = cmd_input.split(maxsplit=2)
            if fields[0] in ('create', 'join', 'quit', 'cancel') and self.userInfo is None:
                print('[Error]: Please login first')
                return True
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
                        self.quit_conference()
                    return False
                else:
                    print('[Error]: Invalid command' + '\r\n' + HELP)
            elif len(fields) == 2:
                arg = fields[1]
                if fields[0] == 'join' and arg.isdigit():
                    self.join_conference(arg)
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
                print('[Error]: Invalid command' + '\r\n' + HELP)
            return True    


if __name__ == '__main__':
    client1 = ConferenceClient()
    client1.start()

