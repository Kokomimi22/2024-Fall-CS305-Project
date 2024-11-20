class User:
    def __init__(self, uuid, username='default', password='password'):
        self.username = username
        self.password = password
        self.uuid = uuid
        self.addr = None  # (ip, port)

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