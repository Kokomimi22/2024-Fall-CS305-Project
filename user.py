from config import *
from util import *

class User:
    def __init__(self, uuid, username='default', password='password'):
        self.username = username
        self.password = password
        self.uuid = uuid
        self.addr = None  # (ip, port)
        self.is_active = False # is user online

    def __repr__(self):
        return f'<User {self.username}>'

    def __str__(self):
        return f'User {self.username} {self.uuid}'

    def __eq__(self, other):
        return self.uuid == other.uuid

    def update(self, username=None, password=None):
        if username:
            self.username = username
        if password:
            self.password = password

    def assign_addr(self, ip, port):
        self.addr = (ip, port)

class UserManager:
    def __init__(self):
        self.users = {}
        self.UUIDManager = UUID()

    def register(self, username, password):
        uuid = self.UUIDManager.generate_uuid()
        user = User(uuid, username, password)
        self.users[uuid] = user
        return user

    def login(self, uuid, password):
        user = self.users.get(uuid)
        if user and user.password == password:
            user.is_active = True
            return user
        return None

    def logout(self, uuid):
        user = self.users.get(uuid)
        if user:
            user.is_active = False
            return user
        return None

    def get_user(self, uuid):
        return self.users.get(uuid)

    def get_all_users(self):
        return self.users

    def remove_user(self, uuid):
        return self.users.pop(uuid)

    def update_user(self, uuid, username=None, password=None):
        user = self.users.get(uuid)
        if user:
            user.update(username, password)
            return user
        return None

    def is_active(self, uuid):
        '''
        check if user is active, for some login required operations
        :param uuid: str, uuid in hex
        :return: bool, True if user is active
        '''
        return self.users.get(uuid).is_active

    def load(self):
        try:
            with open(USER_INFO_FILE, 'r') as f:
                data = json.load(f)
                for uuid, user in data.items():
                    self.users[uuid] = User(uuid, user['username'], user['password'])
                print('User info loaded')
        except FileNotFoundError:
            print('No user info file found, initializing...')
            pass

    def save(self):
        with open(USER_INFO_FILE, 'w') as f:
            json.dump(self.users, f, default=lambda x: x.__dict__)