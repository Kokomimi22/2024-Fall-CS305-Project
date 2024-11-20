import uuid

class UUID:
    def __init__(self):
        '''
        initialize the uuids manager for conference
        '''
        self.uuids = []

    def generate_uuid(self):
        '''
        generate a new uuid for conference
        :return: str
        '''
        new_uuid = str(uuid.uuid4())
        while new_uuid in self.uuids:
            new_uuid = str(uuid.uuid4())
        self.uuids.append(new_uuid)
        return new_uuid

    def remove_uuid(self, uuid):
        '''
        remove the uuid from the list
        :param uuid: str
        '''
        self.uuids.remove(uuid)

from enum import Enum

class Mode(Enum):
    """Enum for the different modes of the program."""
    P2P = 1
    C2S = 0