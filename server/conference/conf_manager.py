from conference.interface import Conference
from user import User
from utils import UUID

class ConferenceManager():
    def __init__(self):
        self.existing_conferences = {} # {conference_id: Conference}
        self.uuid_handler = UUID()

    def list_conferences(self):
        '''
        Get all existing conferences
        :return: dict
        '''
        return self.existing_conferences

    def add_conference(self, conf, conf_id):
        '''
        '''
        if conf_id in self.existing_conferences:
            return None, ConferenceError(True, 'Conference has been added')
        existing_conferences[conf_id] = conf
        return None, ConferenceError()

    def create_conference(self, conf_config, creator):
        '''
        Create a new conference entity

        :param conf_config: dict { 'conf_name': str, 'supervisor': User }
        :param creator: User
        '''
        new_conf = Conference(server=sock, uuid=self.uuid_handler.generate_uuid(), supervisor=creator)
        return self.add_conference(conf=new_conf, conf_id=new_conf.conference_id)

    def remove_conference(self, conf_id, operator):
        '''
        '''
        if conf_id in self.existing_conferences:
            waste_conf = self.existing_conferences.pop(conf_id)
            waste_uuid = waste_conf.conference_id
            self.uuid_handler.remove_uuid(waste_uuid)
            return True
        else:
            return False

    def get_conference_byUUID(self, _conf_id):
        if _conf_id in self.existing_conferences:
            return self.existing_conferences[_conf_id], True
        else:
            return None, False

    def join_conference(self, user, conf_id):
        conf, err = get_conference_byUUID(conf_id)
        if err.Error():
            return None, err
        if user in conf.connected_clients:
            return None, ConferenceError(True, f'You have already joined this conference: {conf_id}')
        else:
            conf.add_client(user)
            return None, ConferenceError()

    def leave_conference(self, user, conf_id):
        conf, err = get_conference_byUUID(conf_id)
        if err.Error():
            return None, err
        if user in conf.connected_clients:
            return None, ConferenceError()
        else:
            conf


class ConferenceError:
    def __init__(self, err=False, _err_msg=None):
        self.err = err
        self.err_msg = _err_msg

    def error():
        return self.err

    @classmethod
    def default(cls):
        return cls()

    def display():
        if self.err:
            return self.err_msg