import asyncio
import json
import struct
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
        # 检查是否是终止信号，如果是则删除客户端
        client_id_len = struct.unpack_from("I", data)[0]
        offset = struct.calcsize("I")
        client_id = data[offset:offset + client_id_len].decode('utf-8')
        offset += (client_id_len + struct.calcsize("Q") + struct.calcsize("I"))
        chunk_data = data[offset:]
        if chunk_data == b'TERMINATE':
            self.server.clients_addr['video'].pop(client_id, None)
        await self.server.handle_video(data, addr)



