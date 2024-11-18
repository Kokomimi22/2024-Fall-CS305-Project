from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
from time import sleep
from enum import Enum

from shared.interface import *
from shared.config import SERVER_IP, UDP_SERVER_PORT

class UDPServer:
    def __init__(self, httpserver):
        self.server = socket(AF_INET, SOCK_DGRAM)
        self.server.bind((SERVER_IP, UDP_SERVER_PORT))
        self.httpserver = httpserver

    def handle(self, socket):
        while True:
            try:
                data, addr = self.server.recvfrom(4096)
                udpmessage_type, msg = parse_msg(data)
                print(f"Received data: {data}")
                self.httpserver.handle(data)
            except Exception as e:
                print(f"Error: {e}")

    def run(self):
        thread = Thread(target=self.handle)
        thread.start()

        while True:
            sleep(1)

    def log(self, level, record):
        pass

    def parse_msg(self, msg):
        '''
        parse the UDP message from clients

        :param msg: bytes
        :return: UDPMessage, Union[str, bytes]
        '''
        if msg[0] == 1:
            return UDPMessage.JOIN, msg[1:].decode('utf-8')
        elif msg[0] == 2:
            return UDPMessage.LEAVE, msg[1:].decode('utf-8')
        elif msg[0] == 3:
            return UDPMessage.AUDIO, msg[1:]
        elif msg[0] == 4:
            return UDPMessage.VIDEO, msg[1:]
        elif msg[0] == 5:
            return UDPMessage.IGNORE, None
        else:
            return UDPMessage.ERROR, 'unknown udp message heading'

    def join(self, client, conf_id):
        confs = httpserver.existing_conferences
        for conf in confs:
            if conf.conference_id == conf_id:
                conf.connected_streams.append(client)
                return True
        return False

    def leave(self, client, conf_id):
        confs = httpserver.existing_conferences
        for conf in confs:
            if conf.conference_id == conf_id:
                conf.connected_streams.remove(client)
                return True
        return False

    def emit(self, msg, _type, client):
        if _type != UDPMessage.AUDIO or _type != UDPMessage.VIDEO:
            return
        
        confs = httpserver.existing_conferences
        for conf in confs:
            if client in conf.connected_streams:
                for _conf in confs:
                    if _conf != conf:
                        self.server.sendto(msg, client)
                return True
        return False



class UDPMessage(Enum):
    JOIN = 1
    LEAVE = 2
    AUDIO = 3
    VIDEO = 4
    ERROR = 5
    IGNORE = 6