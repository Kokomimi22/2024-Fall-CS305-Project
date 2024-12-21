import json
from enum import Enum
from typing import Dict, Tuple

from config import MessageType


class DistributeProtocol(Enum):
    CLIENT_SERVER = 'Client-Server'
    PEER_TO_PEER = 'Peer-to-Peer'

class ProtocolUpgradeFormat:
    def __init__(self, target_protocol: DistributeProtocol):
        self.target_protocol = target_protocol
        self.peer_addr = {}

    def pack(self):
        raise NotImplementedError()

    @staticmethod
    def unpack(data):
        raise NotImplementedError()

class ProtocolInitialFormat(ProtocolUpgradeFormat):
    def __init__(self, local_addr: Dict[str, Tuple[str, int]], client_id: str):
        super().__init__(DistributeProtocol.PEER_TO_PEER)
        self.peer_addr = local_addr
        self.client_id = client_id

    def pack(self):
        return {
            'type': MessageType.INIT.value,
            'client': self.client_id,
            'local_addr': self.peer_addr
        }

    @staticmethod
    def unpack(data):
        """
        :return: local_addr, client_id
        """
        try:
            if data.get('type') == MessageType.INIT.value:
                return data['local_addr'], data['client']
        except KeyError:
            raise ValueError('Invalid data format')

class ProtocolUpgradeServerFormat(ProtocolUpgradeFormat):
    def __init__(self, target_protocol: DistributeProtocol, request_map: Dict[Tuple[str, int], Dict[str, Tuple[str, int]]]):
        super().__init__(target_protocol)
        self.peer_addr = request_map

    def pack(self, target_addr: Tuple[str, int]):
        if self.target_protocol == DistributeProtocol.CLIENT_SERVER:
            return {
                'type': MessageType.UPGRADE.value,
                'target_protocol': self.target_protocol.value,
            }
        else:
            return {
                'type': MessageType.UPGRADE.value,
                'target_protocol': self.target_protocol.value,
                'peer_addr': self.peer_addr[target_addr]
            }

    def unpack(data):
        """
        :return: target_protocol, peer_addr
        """
        try:
            if data.get('type') == MessageType.UPGRADE.value:
                if data.get('target_protocol') == DistributeProtocol.CLIENT_SERVER.value:
                    return data['target_protocol'], None
                else:
                    return data['target_protocol'], data['peer_addr']
        except KeyError:
            raise ValueError('Invalid data format')


class ProtocolControl:
    def __init__(self, server):
        self.protocol = DistributeProtocol.PEER_TO_PEER
        self.client_num = 0
        self.server = server

    def upgradeToClientServer(self):
        self.protocol = DistributeProtocol.CLIENT_SERVER
        # send upgrade message to clients
        for reader, writer in self.server.clients_conns_text.values():
            upgrade_request = ProtocolUpgradeServerFormat(DistributeProtocol.CLIENT_SERVER, None).pack()
            writer.write(json.dumps(upgrade_request).encode())

    def upgradeToPeerToPeer(self):
        self.protocol = DistributeProtocol.PEER_TO_PEER
        # send upgrade message to clients
        _, writer1 = self.server.clients_conns_text.values()[0]
        _, writer2 = self.server.clients_conns_text.values()[1]
        upgrade_request = ProtocolUpgradeServerFormat(DistributeProtocol.PEER_TO_PEER, {
            writer1.get_extra_info('peername'): self.client_local_addr[writer1],
            writer2.get_extra_info('peername'): self.client_local_addr[writer2]
        })

    def addClient(self):
        next_client_num = self.client_num + 1
        if next_client_num > 2 and self.protocol == DistributeProtocol.PEER_TO_PEER:
            self.upgradeToClientServer()
        self.client_num = next_client_num

    def removeClient(self):
        next_client_num = self.client_num - 1
        if next_client_num == 2 and self.protocol == DistributeProtocol.CLIENT_SERVER:
            self.upgradeToPeerToPeer()
        self.client_num = next_client_num