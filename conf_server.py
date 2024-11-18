import asyncio
import random
import threading
from http.client import responses
from config import *
from util import *


import asyncio

class ConferenceServer:
    def __init__(self, manager, conference_id, conf_serve_ports):
        #the ip address of the manager
        self.manager = str(manager).split(',')[0]
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
            data = await reader.read(1024)
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
        try:
            while self.running:
                data = await reader.read(100)
                if not data:
                    break
                print(f"Received: {data.decode()} from {addr}")
                message = data.decode()
                if message.startswith('share'):
                    data_type = message.split()[1]
                    await self.handle_data(reader, writer, data_type)
                elif message.startswith('quit'):
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
                writer.write(b'Cancelled')
                writer.close()
                await writer.wait_closed()
                print(f"Client {addr} has left the conference.")

    async def log(self):
        while self.running:
            print(f"Conference {self.conference_id} running with clients: {self.clients_info}")
            await asyncio.sleep(5)

    async def stop(self):
        self.running = False
        await self.cancel_conference()
        self.loop.stop()

    async def cancel_conference(self):
        """
        Disconnect all connections to cancel the conference.
        """
        print(f"Attempting to cancel conference {self.conference_id}...")
        tasks = asyncio.all_tasks(self.loop)
        for task in tasks:
            task.cancel()
        print(f"Conference {self.conference_id} successfully cancelled.")
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
            server.close()
            self.loop.run_until_complete(server.wait_closed())
            #avoid RuntimeError: Event loop is closed
            if self.running:
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

    def handle_creat_conference(self, addr):
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
        conference_server = ConferenceServer(addr, conference_id, conference_port)
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

    async def handle_cancel_conference(self, conference_id, addr=None):
        """
        cancel conference (in-meeting request, a ConferenceServer should be closed by the MainServer)
        """
        if conference_id in self.conference_servers:
            manager_addr = self.conference_servers[conference_id].manager
            client_addr = str(addr).split(',')[0]
            if manager_addr != client_addr:
                return "Permission denied"
            conference_server = self.conference_servers[conference_id]
            asyncio.run_coroutine_threadsafe(conference_server.stop(), conference_server.loop)
            del self.conference_servers[conference_id]
            response = f"Cancelled conference {conference_id}"
        else:
            response = f"Conference {conference_id} not found"
        return response
    async def request_handler(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received: {message} from {addr}")

        if message.startswith('create'):
           response = self.handle_creat_conference(addr=addr)

        elif message.startswith('join'):
            response = self.handle_join_conference(conference_id=int(message.split(' ')[1]))

        elif message.startswith('cancel'):
            response = await self.handle_cancel_conference(conference_id=int(message.split(' ')[1]), addr=addr)
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
                    await conference_server.cancel_conference()

    def start(self):
        """
        start MainServer
        """
        print(f"MainServer started at {self.server_ip}:{self.server_port}")
        asyncio.run(self.start_server())


if __name__ == '__main__':
    server = MainServer(SERVER_IP, MAIN_SERVER_PORT)
    server.start()
