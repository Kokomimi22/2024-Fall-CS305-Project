import asyncio
import random
import socket
import threading
from codecs import StreamWriter, StreamReader
import json
from Protocol.VideoProtocol import VideoProtocol
from common.user import *

class ConferenceServer:
    def __init__(self, manager_id: str, conference_id: int, conf_serve_port: int):
        self.transport: Dict[str, asyncio.DatagramTransport] = {} # self.transport[datatype] = transport
        # the uuid of the manager of the conference
        self.manager_id: str = manager_id  # str(uuid)
        self.conference_id: int = conference_id
        self.conf_serve_port: int = conf_serve_port
        self.data_serve_ports = {}
        self.data_types: List[str] = ['screen', 'camera', 'audio', 'text']
        self.clients_info = []
        self.client_conns = {}
        # self.clients_addr[datatype][client_id] = addr
        # ,it is used to store the address of the client when transmitting screen, camera, and audio data
        self.clients_addr = {datatype: {} for datatype in self.data_types if datatype != 'text'}
        self.mode = 'Client-Server'
        self.running = True
        self.loop = asyncio.new_event_loop()

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        """
        Handle in-meeting requests or messages from clients.
        """
        addr = writer.get_extra_info('peername')
        self.clients_info.append(addr)
        self.client_conns[addr] = (reader, writer)
        client_id = None
        try:
            while self.running:
                data = await reader.read(CONTROL_LINE_BUFFER)
                if not data:
                    break
                message = data.decode()
                print(f"Received: {message} from {addr}")
                request = json.loads(message)
                if request['type'] == MessageType.QUIT.value:
                    break
                elif request['type'] == MessageType.INIT.value:
                    client_id = request['client_id']
                elif request['type'] == MessageType.TEXT_MESSAGE.value:
                    sender_name = request.get('sender_name', 'undefined')
                    await self.emit_message(request['message'], sender_name, writer)
                else:
                    print(f"Unknown message: {message}")
        except asyncio.CancelledError:
            pass
        except ConnectionResetError:
            print(f"Connection reset by peer {addr}")
        finally:
            del self.client_conns[addr]
            self.clients_info.remove(addr)
            # judge if the writer is closed
            if not writer.is_closing():
                try:
                    writer.write(b'Cancelled')
                    await writer.drain()
                except (ConnectionResetError, BrokenPipeError):
                    print(f"Failed to send 'Cancelled' message to {addr} because the connection was closed.")
                writer.close()
                try:
                    await asyncio.wait_for(writer.wait_closed(), timeout=5)
                except asyncio.TimeoutError:
                    print(f"Waiting for {addr} to close timed out.")
                print(f"Client {addr} has left the conference.")
            if self.running and client_id == self.manager_id:
                await self.stop()

    async def emit_message(self, message: str, sender_name: str, sender: StreamWriter):
        """
        Send a message to all clients in the conference.
        """
        emit_message = {
            'type': MessageType.TEXT_MESSAGE.value,
            'message': message,
            'sender_name': sender_name
        }
        for client_reader, client_writer in self.client_conns.values():
            if client_writer != sender:
                client_writer.write(json.dumps(emit_message).encode())
                await client_writer.drain()

    async def handle_video(self, data, addr):
        for client_addr in self.clients_addr['camera'].values():
            if client_addr != addr:
                self.transport['camera'].sendto(data, client_addr)

    async def log(self):
        try:
            while self.running:
                print(f"Conference {self.conference_id} running with clients: {self.clients_info}")
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass

    async def stop(self):
        self.running = False
        await self.cancel_conference()
        self.loop.stop()


    async def cancel_conference(self):
        """
        Disconnect all connections to cancel the conference.
        """
        print(f"Attempting to cancel conference {self.conference_id}...")
        # Cancel all tasks
        tasks = [task for task in asyncio.all_tasks(self.loop) if task is not asyncio.current_task()]
        success = np.array([task.cancel() for task in tasks])
        for client_addr in self.clients_addr['camera'].values():
            self.transport['camera'].sendto(b'Cancelled', client_addr)
        await asyncio.gather(*tasks, return_exceptions=True)
        if success.all():
            print(f"Conference {self.conference_id} successfully cancelled.")
        else:
            print(f"Failed to cancel conference {self.conference_id}.")

    def start(self):
        server_coro = asyncio.start_server(self.handle_client, '127.0.0.1', self.conf_serve_port)
        video_server_coro = self.loop.create_datagram_endpoint(
            lambda: VideoProtocol(self),
            local_addr=('127.0.0.1', self.data_serve_ports['camera'])
        )
        server = self.loop.run_until_complete(server_coro)
        self.transport['camera'], _ = self.loop.run_until_complete(video_server_coro)
        self.loop.create_task(self.log())
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.loop.stop()
        except Exception as e:
            print(f"Error: {e}")
            self.loop.stop()
        finally:
            if not self.loop.is_closed():
                server.close()
                for transport in self.transport.values():
                    transport.close()
                self.loop.run_until_complete(server.wait_closed())
                if self.running:
                    self.running = False
                    self.loop.run_until_complete(self.cancel_conference())
                self.loop.close()


class MainServer:
    def __init__(self, server_ip, main_port):
        # async server
        self.server_ip = server_ip
        self.server_port = main_port
        self.main_server = None

        self.conference_conns = {}  # self.conference_conns[conference_id] = (reader, writer)
        self.conference_servers = {}  # self.conference_servers[conference_id] = ConferenceManager
        self.user_manager = UserManager()

    @staticmethod

    def handle_get_conferences(self):
        """
        get all conferences
        """
        return {
            'status': Status.SUCCESS.value,
            'conferences': list(self.conference_servers.keys())
        }

    def handle_create_conference(self, client_id: str) -> Dict[str, Any]:
        """
        create conference: create and start the corresponding ConferenceServer, and reply necessary info to client
        """
        # 生成唯一的会议id
        conference_id = random.randint(1000, 9999)
        while conference_id in self.conference_servers:
            conference_id = random.randint(1000, 9999)

        # 会议服务器的端口号
        conference_port = get_port()
        conference_server = ConferenceServer(client_id, conference_id, conference_port)
        # 为会议服务器的每个数据服务器生成端口号
        for dataType in conference_server.data_types:
            conference_server.data_serve_ports[dataType] = get_port()
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
        # 读取json文件，查找是否有对应的用户名和密码
        _user = self.user_manager.login(username, password)
        if _user:
            uuid = _user.uuid
            return {
                'status': Status.SUCCESS.value,
                'uuid': uuid
            }
        return {
            'status': Status.FAILED.value,
            'message': 'Username or password are incorrect'
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
            response = self.handle_create_conference(client_id)
        elif message_type == MessageType.CANCEL.value:
            response = self.handle_cancel_conference(conference_id, client_id)
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
            except (asyncio.CancelledError, KeyboardInterrupt):
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
    server.start()
