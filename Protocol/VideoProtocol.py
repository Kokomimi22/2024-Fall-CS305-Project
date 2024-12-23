import asyncio
import json
from asyncio import DatagramProtocol

from config import MessageType


class VideoProtocol(DatagramProtocol):
    def __init__(self, server):
        self.server = server
    def datagram_received(self, data, addr):
        asyncio.create_task(self.handle_data(data, addr))

    async def handle_data(self, data, addr):
        if addr not in self.server.clients_addr['video'].values():
            request = json.loads(data.decode())
            if request.get('type') == MessageType.INIT.value:
                client_id = request['client_id']
                self.server.clients_addr['video'][client_id] = addr
            return
        await self.server.handle_video(data, addr)



