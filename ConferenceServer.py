import asyncio
from codecs import StreamWriter, StreamReader

from Protocol.AudioProtocol import AudioProtocol
from Protocol.VideoProtocol import VideoProtocol
from common.user import *


class ConferenceServer:
    def __init__(self, manager_id: str, conference_id: int, conf_serve_port: int, conference_name: str, main_server: 'MainServer'):
        self.transport: Dict[str, asyncio.DatagramTransport] = {} # self.transport[datatype] = transport
        # the uuid of the manager of the conference
        self.manager_id: str = manager_id  # str(uuid)
        self.conference_id: int = conference_id
        self.conference_name: str = conference_name
        self.conf_serve_port: int = conf_serve_port
        self.data_serve_ports = {}
        self.data_types: List[str] = ['video', 'audio', 'text']
        self.mixed_audio_buffer = {}
        self.clients_info = []
        self.client_conns_text = {} # self.client_conns_text[addr] = (reader, writer), This is for text data like quit, init, and text message
        """
        self.clients_addr[datatype][client_id] = addr
        ,it is used to store the address of the client when transmitting screen, camera, and audio data
        """
        self.clients_addr = {datatype: {} for datatype in self.data_types}
        self.mode = 'Client-Server'
        self.running = True
        self.loop = asyncio.new_event_loop()
        self.main_server = main_server

    def get_info(self):
        return {
            'conference_name': self.conference_name,
            'conference_id': self.conference_id,
            'manager_id': self.manager_id,
            'mode': self.mode
        }

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        """
        Handle in-meeting requests or messages from clients.
        """
        addr = writer.get_extra_info('peername')
        self.clients_info.append(addr)
        self.client_conns_text[addr] = (reader, writer)
        self.clients_addr['text'] = addr
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
            del self.client_conns_text[addr]
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
        for client_reader, client_writer in self.client_conns_text.values():
            if client_writer != sender:
                client_writer.write(json.dumps(emit_message).encode())
                await client_writer.drain()

    async def handle_video(self, data, addr):
        for client_addr in self.clients_addr['video'].values():
            self.transport['video'].sendto(data, client_addr)
            #print(f"Sending video data to {client_addr}")

    async def handle_audio(self, data, addr):
        for client_addr in self.clients_addr['audio'].values():
            # if client_addr == addr:
            #     continue
            data = data.ljust(CHUNK * 2, b'\x00')
            mixed_audio = np.add(self.mixed_audio_buffer[client_addr], np.frombuffer(data, dtype=np.int16), casting="unsafe")
            mixed_audio = np.clip(mixed_audio, -32768, 32767)
            self.mixed_audio_buffer[client_addr] = mixed_audio
        self.transport['audio'].sendto(self.mixed_audio_buffer[addr].tobytes(), addr)
        self.mixed_audio_buffer[addr] = np.zeros(CHUNK, dtype=np.int16)

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
            self.main_server.conference_servers.pop(self.conference_id)
        else:
            print(f"Failed to cancel conference {self.conference_id}.")

    def start(self):
        server_coro = asyncio.start_server(self.handle_client, '127.0.0.1', self.conf_serve_port)
        video_server_coro = self.loop.create_datagram_endpoint(
            lambda: VideoProtocol(self),
            local_addr=('127.0.0.1', self.data_serve_ports['video'])
        )
        audio_server_coro = self.loop.create_datagram_endpoint(
            lambda: AudioProtocol(self),
            local_addr=('127.0.0.1', self.data_serve_ports['audio'])
        )
        server = self.loop.run_until_complete(server_coro)
        self.transport['video'], _ = self.loop.run_until_complete(video_server_coro)
        self.transport['audio'], _ = self.loop.run_until_complete(audio_server_coro)
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

