import asyncio
import random
import socket
import threading
import json
from common.user import *
from ConferenceServer import ConferenceServer
class MainServer:
    def __init__(self, server_ip, main_port):
        # async server
        self.server_ip = server_ip
        self.server_port = main_port
        self.main_server = None

        self.conference_conns = {}  # self.conference_conns[conference_id] = (reader, writer)
        self.conference_servers = {}  # self.conference_servers[conference_id] = ConferenceManager
        self.user_manager = UserManager()

    def handle_get_conferences(self):
        """
        get all conferences and infos
        """
        # 删除已经关闭的会议服务器
        to_delete = [conference_id for conference_id, conference_server in self.conference_servers.items() if
                     not conference_server.running]
        for conference_id in to_delete:
            del self.conference_servers[conference_id]
        return {
            'status': Status.SUCCESS.value,
            'conferences': list(self.conference_servers.keys()),
            'conferences_detail': [conference_server.get_info() for conference_server in self.conference_servers.values()]
        }

    def handle_create_conference(self, client_id: str, conference_name: str) -> Dict[str, Any]:
        """
        create conference: create and start the corresponding ConferenceServer, and reply necessary info to client
        """
        # 生成唯一的会议id
        conference_id = random.randint(1000, 9999)
        while conference_id in self.conference_servers:
            conference_id = random.randint(1000, 9999)

        # 会议服务器的端口号
        conference_port = get_available_port()
        client_name = self.user_manager.get_user(client_id).username
        conference_server = ConferenceServer(
            client_id,
            client_name,
            conference_id,
            conference_port,
            conference_name)
        # 为会议服务器的每个数据服务器生成端口号
        for dataType in conference_server.data_types:
            conference_server.data_serve_ports[dataType] = get_available_port()
        self.conference_servers[conference_id] = conference_server
        # 启动会议服务器
        conference_thread = threading.Thread(target=conference_server.start)
        conference_thread.start()
        print(f"Created conference {conference_id} with port {conference_port}")
        return {
            'status': Status.SUCCESS.value,
            'conference_id': conference_id,
        }

    def handle_join_conference(self, conference_id: int) -> Dict[str, Any]:
        """
        join conference: search corresponding conference_info and ConferenceServer, and reply necessary info to client
        """
        if conference_id in self.conference_servers.keys():
            conference_server = self.conference_servers[conference_id]
            return {
                'status': Status.SUCCESS.value,
                'conference_id': conference_id,
                'data_serve_ports': conference_server.data_serve_ports,
                'conference_serve_port': conference_server.conf_serve_port
            }

        return {
            'status': Status.FAILED.value,
            'message': f"Conference {conference_id} not found"
        }

    def handle_register(self, username, password):
        """
        register a new user
        """
        # 生成一个唯一的uuid，储存到json文件中
        _new_user = self.user_manager.register(username, password)
        if _new_user:
            return {
                'status': Status.SUCCESS.value,
            }
        return {
            'status': Status.FAILED.value,
            'message': 'Register Failed'
        }

    def handle_login(self, username, password):
        """
        login an existing user
        """
        # 读取json文件，查找是否有对应的用户名和密码, 并且检查是否已经登录以及是否正确
        _user = self.user_manager.login(username, password)
        if _user == User("1"):
            return {
                'status': Status.FAILED.value,
                'message': 'User already logged in'
            }
        if _user == User("2"):
            return {
                'status': Status.FAILED.value,
                'message': 'Username or password are incorrect'
            }
        uuid = _user.uuid
        return {
            'status': Status.SUCCESS.value,
            'uuid': uuid
        }

    def handle_logout(self, uuid):
        """
        logout an existing user
        """
        # 读取json文件，查找是否有对应的uuid
        _user = self.user_manager.logout(uuid)
        if _user:
            return {
                'status': Status.SUCCESS.value,
            }
        return {
            'status': Status.FAILED.value,
            'message': 'User not found'
        }

    def handle_cancel_conference(self, conference_id, client_id=None):
        """
        cancel conference (in-meeting request, a ConferenceServer should be closed by the MainServer)
        """
        if conference_id in self.conference_servers:
            manager_uuid = self.conference_servers[conference_id].manager_id
            if client_id != manager_uuid:
                return {
                    'status': Status.FAILED.value,
                    'message': 'You are not the manager of this conference'
                }
            conference_server = self.conference_servers[conference_id]
            asyncio.run_coroutine_threadsafe(conference_server.stop(), conference_server.loop)
            if conference_id in self.conference_servers:
                del self.conference_servers[conference_id]
            return {
                'status': Status.SUCCESS.value
            }
        return {
            'status': Status.FAILED.value,
            'message': f"Conference {conference_id} not found"
        }

    async def request_handler(self, reader, writer):
        data = await reader.read(CONTROL_LINE_BUFFER)
        message = data.decode().strip()

        print(f"Received: {message} from {writer.get_extra_info('peername')}")
        fields: Dict[str, Any] = json.loads(message)

        client_id = fields.get('client_id')
        conference_id = fields.get('conference_id')
        message_type: str = fields['type']
        if message_type == MessageType.JOIN.value:
            response = self.handle_join_conference(conference_id)
        elif message_type == MessageType.LOGOUT.value:
            response = self.handle_logout(client_id)
        elif message_type == MessageType.REGISTER.value:
            response = self.handle_register(fields.get('username'), fields.get('password'))
        elif message_type == MessageType.LOGIN.value:
            response = self.handle_login(fields.get('username'), fields.get('password'))
        elif message_type == MessageType.CREATE.value:
            response = self.handle_create_conference(client_id, fields.get('conference_name'))
        elif message_type == MessageType.CANCEL.value:
            response = self.handle_cancel_conference(conference_id, client_id)
        elif message_type == MessageType.GET_CONFERENCES.value:
            response = self.handle_get_conferences()
        else:
            response = {
                'status': Status.FAILED.value,
                'message': 'Unknown command'
            }
        writer.write(json.dumps(response).encode())
        await writer.drain()

        writer.close()
        await writer.wait_closed()

    async def start_server(self):
        server = await asyncio.start_server(self.request_handler, self.server_ip, self.server_port)
        async with server:
            try:
                await server.serve_forever()
            except asyncio.CancelledError:
                pass
            finally:
                for conference_server in self.conference_servers.values():
                    asyncio.run_coroutine_threadsafe(conference_server.stop(), conference_server.loop)

    def start(self):
        """
        start MainServer
        """
        print(f"MainServer started at {self.server_ip}:{self.server_port}")
        self.user_manager.load()
        asyncio.run(self.start_server())
if __name__ == '__main__':
    server = MainServer(SERVER_IP, MAIN_SERVER_PORT)
    try:
        server.start()
    except KeyboardInterrupt:
        print("Server stopped")
