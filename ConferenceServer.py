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
        self.data_types: List[str] = ['video', 'audio', 'text']
        self.clients_info = []
        self.client_conns = {} # self.client_conns[addr] = (reader, writer), This is for text data like quit, init, and text message
        """
        self.clients_addr[datatype][client_id] = addr
        ,it is used to store the address of the client when transmitting screen, camera, and audio data
        """
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
        for client_addr in self.clients_addr['video'].values():
            if client_addr != addr:
                self.transport['video'].sendto(data, client_addr)

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
        for client_addr in self.clients_addr['video'].values():
            self.transport['video'].sendto(b'Cancelled', client_addr)
        await asyncio.gather(*tasks, return_exceptions=True)
        if success.all():
            print(f"Conference {self.conference_id} successfully cancelled.")
        else:
            print(f"Failed to cancel conference {self.conference_id}.")

    def start(self):
        server_coro = asyncio.start_server(self.handle_client, '127.0.0.1', self.conf_serve_port)
        video_server_coro = self.loop.create_datagram_endpoint(
            lambda: VideoProtocol(self),
            local_addr=('127.0.0.1', self.data_serve_ports['video'])
        )
        server = self.loop.run_until_complete(server_coro)
        self.transport['video'], _ = self.loop.run_until_complete(video_server_coro)
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

