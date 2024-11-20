class User:
    def __init__(self, username, password, uuid):
        self.username = username
        self.password = password
        self.uuid = uuid
        self.addr = None #(ip, port)

    def __init__(self, uuid):
        self.username = 'default'
        self.password = 'password'
        self.uuid = uuid

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

    def assgin_addr(self, addr):
        self.addr = addr

    def assgin_addr(self, ip, port):
        self.addr = (ip, port)
    