import asyncio
from asyncio import StreamReader, StreamWriter


class TextServer:

    CACHE_SIZE = 10 # max cache size

    def __init__(self):
        self.clients = [] # type: list[(StreamReader, StreamWriter)]
        self.cache = [] # type: list[bytes]

    def update_clients(self, clients: list[(StreamReader, StreamWriter)]):
        self.clients = clients

    def cacheData(self, data: bytes):
        if len(self.cache) >= self.CACHE_SIZE:
            self.cache.pop(0)
        self.cache.append(data)

    async def emit(self, data: bytes, sender_writer: StreamWriter):
        self.cacheData(data)
        for reader, writer in self.clients:
            if writer != sender_writer:
                await self._emitTo([data], writer)

    async def emitCache(self, writer: StreamWriter):
        if self.cache:
            await self._emitTo(self.cache, writer)

    @staticmethod
    async def _emitTo(data: list[bytes], writer: StreamWriter):
        for d in data:
            writer.write(d)
            await writer.drain()
            await asyncio.sleep(0.1)