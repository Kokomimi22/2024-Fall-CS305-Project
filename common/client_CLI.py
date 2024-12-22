import traceback

from common.conf_client import *

class ClientCLI:
    def __init__(self, client):
        self.client = client

    def start(self):
        """
        execute functions based on the command line input
        """
        try:
            while True:
                if not self.client.on_meeting:
                    status = 'Free'
                else:
                    status = f'OnMeeting-{self.client.conference_id}'

                cmd_input = input(f'({status}) Please enter a operation (enter "?" to help): ')
                continue_flag = self.command_parser(cmd_input)
                if not continue_flag:
                    break
        except Exception as e:
            traceback.print_exc()
            print(f'[Error]: {e}')
        finally:
            if self.client.userInfo:
                self.client.logout()

    def command_parser(self, cmd_input):
        """
            parse the command line input and execute the corresponding functions
            """
        cmd_input = cmd_input.strip().lower().strip()
        fields = cmd_input.split(maxsplit=2)
        if not fields:
            return True
        if fields[0] in ('create', 'join', 'quit', 'cancel') and self.client.userInfo is None:
            print('[Error]: Please login first')
            return True
        if len(fields) == 1:
            if cmd_input in ('?', '？'):
                print(HELP)
            elif cmd_input == 'create':
                self.client.create_conference('default')
            elif cmd_input == 'quit':
                self.client.quit_conference()
            elif cmd_input == 'cancel':
                self.client.cancel_conference()
            elif cmd_input == 'exit':
                return False
            elif cmd_input == 'logout':
                self.client.logout()
            elif cmd_input == 'get_conferences':
                self.client.get_conference_list()
            elif cmd_input == 'switch_video_mode':
                self.client.switch_video_mode()
            else:
                print('[Error]: Invalid command' + '\r\n' + HELP)
        elif len(fields) == 2:
            arg = fields[1]
            if fields[0] == 'join' and arg.isdigit():
                self.client.join_conference(int(arg))
            elif fields[0] == 'on':
                if arg == 'camera':
                    self.client.start_video_sender('camera')
                elif arg == 'screen':
                    self.client.start_video_sender('screen')
                elif arg == 'audio':
                    self.client.start_send_audio()
                else:
                    print('[Error]: Invalid command' + '\r\n' + HELP)
            elif fields[0] == 'off':
                if arg == 'video':
                    self.client.stop_video_sender()
                elif arg == 'audio':
                    self.client.stop_send_audio()
                else:
                    print('[Error]: Invalid command' + '\r\n' + HELP)
            elif fields[0] == 'text':
                self.client.send_message(arg)
            else:
                print('[Error]: Invalid command' + '\r\n' + HELP)
        elif len(fields) == 3:
            arg1, arg2 = fields[1], fields[2]
            if fields[0] == 'register':
                self.client.register(arg1, arg2)
            elif fields[0] == 'login':
                self.client.login(arg1, arg2)
            else:
                print('[Error]: Invalid command' + '\r\n' + HELP)
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER_IP, MAIN_SERVER_PORT))
                s.sendall(cmd_input.encode())
                self.client.recv_data = s.recv(CONTROL_LINE_BUFFER).decode('utf-8')
                print(f'[Info]: {self.client.recv_data}')
        return True

if __name__ == '__main__':
    client = ConferenceClient()
    client_cli = ClientCLI(client)
    client_cli.start()