import asyncio
import json
import random
import threading
from http.client import responses

from pyexpat.errors import messages

from config import *
from util import *
from user import *

import asyncio

class ConferenceServer:
    def __init__(self, manager, conference_id, conf_serve_ports):
        #the ip address of the manager
        self.manager = manager #str(uuid)
        self.conference_id = conference_id
        self.conf_serve_ports = conf_serve_ports
        self.data_serve_ports = {}
        self.data_types = ['screen', 'camera', 'audio']
        self.clients_info = []
        self.client_conns = {}
        self.mode = 'Client-Server'
        self.running = True
        self.loop = asyncio.new_event_loop()

    async def handle_data(self, reader, writer, data_type):
        """
        Receive sharing stream data from a client and forward it to the rest of the clients.
        """
        while self.running:
            data = await reader.read(DATA_LINE_BUFFER)
            if not data or data == b'end':
                break
            for client_reader, client_writer in self.client_conns.values():
                if client_writer != writer:
                    client_writer.write(data)
                    await client_writer.drain()

    async def handle_client(self, reader, writer):
        """
        Handle in-meeting requests or messages from clients.
        """
        addr = writer.get_extra_info('peername')
        self.clients_info.append(addr)
        self.client_conns[addr] = (reader, writer)
        user_uuid = None
        try:
            while self.running:
                data = await reader.read(CONTROL_LINE_BUFFER)
                if not data:
                    break
                message = data.decode()
                print(f"Received: {message} from {addr}")
                fields = data.decode().split(' ')
                if fields[0] == 'share':
                    data_type = fields[1]
                    await self.handle_data(reader, writer, data_type)
                elif fields[0] == 'init':
                    user_uuid = fields[1]
                    writer.write(f"Welcome to conference {self.conference_id}".encode())
                    await writer.drain()
                elif fields[0] == 'quit':
                    print(f"Client {addr} has requested to quit the conference.")
                    writer.write(b'Quitted')
                    break
                else:
                    print(f"Unknown message: {message}")
        except asyncio.CancelledError:
            pass
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
                    await asyncio.wait_for(writer.wait_closed(), timeout=5)  # set a timeout to wait for the writer to close
                except asyncio.TimeoutError:
                    print(f"Waiting for {addr} to close timed out.")
                print(f"Client {addr} has left the conference.")
            # judge if the manager has left the conference
            if user_uuid == self.manager and self.running:
                await self.stop()

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
        # cancel all tasks
        cancel_success = [task.cancel() for task in asyncio.all_tasks(self.loop) if task is not asyncio.current_task()]
        if all(cancel_success):
            print(f"Conference {self.conference_id} successfully cancelled.")
        else:
            print(f"Failed to cancel conference {self.conference_id}.")
        #self.loop.stop()

    def start(self):
        """
        Start the ConferenceServer and necessary running tasks to handle clients in this conference.
        """
        server_coro = asyncio.start_server(self.handle_client, '127.0.0.1', self.conf_serve_ports)
        server = self.loop.run_until_complete(server_coro)
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

    def handle_create_conference(self, uuid):
        """
        create conference: create and start the corresponding ConferenceServer, and reply necessary info to client
        """
        # Generate a unique conference_id
        conference_id = random.randint(1000, 9999)
        while conference_id in self.conference_servers:
            conference_id = random.randint(1000, 9999)

        # Generate a unique conference_port
        conference_port = random.randint(10000, 65535)
        existing_ports = [server.conf_serve_ports for server in self.conference_servers.values()]
        while conference_port in existing_ports:
            conference_port = random.randint(10000, 65535)

        # Create and store the new ConferenceServer
        conference_server = ConferenceServer(uuid, conference_id, conference_port)
        self.conference_servers[conference_id] = conference_server
        # Start the conference server in a new thread
        conference_thread = threading.Thread(target=conference_server.start)
        conference_thread.start()
        print(f"Created conference {conference_id} with ports {conference_port}")
        return f"Created {conference_id}"
        
    def handle_join_conference(self, conference_id):
        """
        join conference: search corresponding conference_info and ConferenceServer, and reply necessary info to client
        """
        if conference_id in self.conference_servers.keys():
            response = f"Joined conference {conference_id} with ports {self.conference_servers[conference_id].conf_serve_ports}"
        else:
            response = f"Conference {conference_id} not found"
        return response

    def handle_quit_conference(self):
        """
        quit conference (in-meeting request & or no need to request)
        """
        pass
    def handle_register(self, username, password):
        """
        register a new user
        """
        # 生成一个唯一的uuid，储存到json文件中
        # TODO: 或许回来可以做一些数据库，使用jwt来进行用户认证等等，目前只是简单的存储到json文件中
        _new_user = self.user_manager.register(username, password)
        if _new_user:
            uuid = _new_user.uuid
            return f"Registered {username} with uuid {uuid}"
        return "Registration failed"

    def handle_login(self, username, password):
        """
        login an existing user
        """
        # 读取json文件，查找是否有对应的用户名和密码
        _user = self.user_manager.login(username, password)
        if _user:
            uuid = _user.uuid
            return f"Logged in {username} with uuid {uuid}"
        return "Login failed"

    def handle_logout(self, uuid):
        """
        logout an existing user
        """
        # 读取json文件，查找是否有对应的uuid
        self.user_manager.logout(uuid)
        return f"Logged out {uuid}"

    def handle_cancel_conference(self, conference_id, uuid=None):
        """
        cancel conference (in-meeting request, a ConferenceServer should be closed by the MainServer)
        """
        if conference_id in self.conference_servers:
            manager_uuid = self.conference_servers[conference_id].manager
            if uuid != manager_uuid:
                return "You are not the manager of this conference"
            conference_server = self.conference_servers[conference_id]
            asyncio.run_coroutine_threadsafe(conference_server.stop(), conference_server.loop)
            del self.conference_servers[conference_id]
            response = f"Cancelled conference {conference_id}"
        else:
            response = f"Conference {conference_id} not found"
        return response
    async def request_handler(self, reader, writer):
        data = await reader.read(CONTROL_LINE_BUFFER)
        message = data.decode().strip()
        addr = writer.get_extra_info('peername')

        print(f"Received: {message} from {addr}")
        fields = message.split(' ')


        if len(fields) == 2:
            if fields[0] == 'join':
                response = self.handle_join_conference(conference_id=int(fields[1]))
            elif fields[0] == 'logout':
                response = self.handle_logout(uuid=fields[1])
            else:
                response = "Unknown command"
        elif len(fields) == 3:
            if fields[0] == 'register':
                response = self.handle_register(fields[1], fields[2])
            elif fields[0] == 'login':
                response = self.handle_login(fields[1], fields[2])
            elif fields[0] == 'create':
               response = self.handle_create_conference(uuid=fields[-1])
            else:
                response = "Unknown command"
        elif len(fields) == 4:
            if fields[0] == 'cancel':
                response = self.handle_cancel_conference(conference_id=int(fields[1]), uuid=fields[-1])
            else:
                response = "Unknown command"
        else:
            response = "Unknown command"

        writer.write(response.encode())
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
