import asyncio
import json
from asyncio import DatagramProtocol
import numpy as np
from config import MessageType, CHUNK


class AudioProtocol(DatagramProtocol):
    def __init__(self, server):
        self.server = server
    def datagram_received(self, data, addr):
        asyncio.create_task(self.handle_data(data, addr))

    async def handle_data(self, data, addr):
        if addr not in self.server.clients_addr['audio'].values():
            request = json.loads(data.decode())
            client_id = request['client_id']
            if request.get('type') == MessageType.INIT.value:
                self.server.clients_addr['audio'][client_id] = addr
                self.server.mixed_audio_buffer[addr] = np.zeros(CHUNK, dtype=np.int16)
            return
        # 处理某个客户端退出的情况
        if data == b'END':
            self.server.clients_addr['audio'] = \
                {k: v for k, v in self.server.clients_addr['audio'].items() if v != addr}
            self.server.mixed_audio_buffer.pop(addr, None)
            return
        await self.server.handle_audio(data, addr)

