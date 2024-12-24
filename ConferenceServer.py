import asyncio
from asyncio import StreamWriter, StreamReader, AbstractEventLoop


from Protocol.AudioProtocol import AudioProtocol
from Protocol.VideoProtocol import VideoProtocol
from common.user import *

class ConferenceServer:
    def __init__(self, manager_id: str, manage_name: str, conference_id: int, conf_serve_port: int, conference_name: str):
        self.transport: Dict[str, asyncio.DatagramTransport] = {}  # self.transport[datatype] = transport
        # the uuid of the manager of the conference
        self.manager_id: str = manager_id  # str(uuid)
        self.manager_name: str = manage_name # str(username)
        self.conference_id: int = conference_id
        self.conference_name: str = conference_name
        self.conf_serve_port: int = conf_serve_port
        self.data_serve_ports = {}
        self.data_types: List[str] = ['video', 'audio', 'text']
        self.mixed_audio_buffer = {}
        self.clients_info = []
        self.client_conns_text = {}  # self.client_conns_text[client_id] = (reader, writer), This is for text data like quit, init, and text message
        """
        self.clients_addr[datatype][client_id] = addr
        ,it is used to store the address of the client when transmitting screen, camera, and audio data
        """
        self.clients_addr = {datatype: {} for datatype in self.data_types}
        self.mode: str = DistributeProtocol.CLIENT_SERVER.value
        self.running: bool = True
        self.loop: AbstractEventLoop = asyncio.new_event_loop()
        self.p2p_ports = {} # self.p2p_ports[client_id] = port, it is used to store the port of the client in peer-to-peer mode

    def get_info(self):
        return {
            'conference_name': self.conference_name,
            'conference_id': self.conference_id,
            'manager_id': self.manager_name,
            'mode': self.mode
        }

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        """
        Handle in-meeting requests or messages from clients.
        """
        addr = writer.get_extra_info('peername')
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
                    self.client_conns_text[client_id] = (reader, writer)
                    self.clients_addr['text'][client_id] = addr
                    self.clients_info.append(addr)
                    await self.switch_mode()
                elif request['type'] == MessageType.TEXT_MESSAGE.value:
                    sender_name = request.get('sender_name', 'undefined')
                    timestamp = request.get('timestamp')
                    await self.emit_message(request['message'], sender_name, timestamp, writer)
                elif request['type'] == MessageType.P2P_INFOS_NOTIFICATION.value:
                    self.p2p_ports[client_id] = request['p2p_info']
                    # notify another client his peer's info
                    message = {
                        'type': MessageType.P2P_INFOS_NOTIFICATION.value,
                        'peer_addr': {
                            'text': (addr[0], self.p2p_ports[client_id]),
                            'video': self.clients_addr['video'][client_id],
                            'audio': self.clients_addr['audio'][client_id]
                        }
                    }
                    for _, self_writer in self.client_conns_text.values():
                        if self_writer != writer:
                            self_writer.write(json.dumps(message).encode())
                            await self_writer.drain()
                else:
                    print(f"Unknown message: {message}")
        except asyncio.CancelledError:
            pass
        except ConnectionResetError:
            print(f"Connection reset by peer {addr}")
        finally:
            self.remove_client(client_id)
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
            if self.mode == DistributeProtocol.PEER_TO_PEER.value:
                self.p2p_ports.pop(client_id, None)
            if self.running and client_id == self.manager_id:
                asyncio.run_coroutine_threadsafe(self.stop(), self.loop)
            if self.running and client_id != self.manager_id:
                asyncio.run_coroutine_threadsafe(self.switch_mode(), self.loop)

    def remove_client(self, client_id: str):
        """
        Remove a client from the conference.
        :param client_id: str
        :return:
        """
        self.client_conns_text.pop(client_id, None)
        if self.clients_addr['text'].get(client_id) in self.clients_info:
            self.clients_info.remove(self.clients_addr['text'][client_id])
        if self.clients_addr['audio'].get(client_id):
            self.mixed_audio_buffer.pop(self.clients_addr['audio'][client_id], None)
        for datatype in self.data_types:
            self.clients_addr[datatype].pop(client_id, None)

    async def switch_mode(self):
        """
        Switch the mode of the conference.
        :return:
        """
        num_clients = len(self.clients_info)
        while set(map(len, self.clients_addr.values())) != {num_clients}:
            await asyncio.sleep(0.1)
        # If there are no clients in the conference, switch to client-server mode
        if num_clients == 1:
            self.mode = DistributeProtocol.CLIENT_SERVER.value
            writer = list(self.client_conns_text.values())[0][1]
            message = {'type': MessageType.SWITCH_TO_CS.value}
            writer.write(json.dumps(message).encode())
            await writer.drain()
        # If there are only two clients in the conference, switch to peer-to-peer mode
        elif num_clients == 2:
            self.mode = DistributeProtocol.PEER_TO_PEER.value
            # Notify all clients to switch to peer-to-peer mode
            for reader, writer in self.client_conns_text.values():
                writer.write(json.dumps({'type': MessageType.SWITCH_TO_P2P.value}).encode())
                await writer.drain()
        # If there are more than two clients in the conference, switch to client-server mode
        elif num_clients > 2:
            # If the mode is already client-server, it does not need to switch
            if self.mode == DistributeProtocol.CLIENT_SERVER.value:
                return
            self.p2p_ports.clear()
            self.mode = DistributeProtocol.CLIENT_SERVER.value
            message = {'type': MessageType.SWITCH_TO_CS.value}
            for reader, writer in self.client_conns_text.values():
                writer.write(json.dumps(message).encode())
                await writer.drain()

    async def emit_message(self, message: str, sender_name: str, timestamp: str, sender: StreamWriter):
        """
        Send a message to all clients in the conference.
        """
        emit_message = {
            'type': MessageType.TEXT_MESSAGE.value,
            'message': message,
            'sender_name': sender_name,
            'timestamp': timestamp
        }
        for client_reader, client_writer in self.client_conns_text.values():
            if client_writer != sender:
                client_writer.write(json.dumps(emit_message).encode())
                await client_writer.drain()

    async def handle_video(self, data, addr):
        """
        Handle video data from clients.
        :param addr: tuple[ip, port]
        :param data: bytes
        :return:
        """
        for client_addr in self.clients_addr['video'].values():
            if client_addr == addr:
                continue
            self.transport['video'].sendto(data, client_addr)
            # print(f"Sending video data to {client_addr}")

    async def handle_audio(self, data, addr):
        """
        Handle audio data from clients.
        :param data: bytes
        :param addr: tuple[ip, port]
        :return:
        """
        for client_addr in self.clients_addr['audio'].values():
            if client_addr == addr:
                continue
            data = data.ljust(CHUNK * 2, b'\x00')
            mixed_audio = np.add(self.mixed_audio_buffer[client_addr], np.frombuffer(data, dtype=np.int16),
                                 casting="unsafe")
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
        await asyncio.gather(*tasks, return_exceptions=True)
        if success.all():
            print(f"Conference {self.conference_id} successfully cancelled.")
        else:
            print(f"Failed to cancel conference {self.conference_id}.")

    def start(self):
        text_server_coro = asyncio.start_server(self.handle_client, SERVER_IP, self.conf_serve_port)
        video_server_coro = self.loop.create_datagram_endpoint(
            lambda: VideoProtocol(self),
            local_addr=(SERVER_IP, self.data_serve_ports['video'])
        )
        audio_server_coro = self.loop.create_datagram_endpoint(
            lambda: AudioProtocol(self),
            local_addr=(SERVER_IP, self.data_serve_ports['audio'])
        )
        text_server = self.loop.run_until_complete(text_server_coro)
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
                text_server.close()
                for transport in self.transport.values():
                    transport.close()
                self.loop.run_until_complete(text_server.wait_closed())
                if self.running:
                    self.running = False
                    self.loop.run_until_complete(self.cancel_conference())
                self.loop.close()