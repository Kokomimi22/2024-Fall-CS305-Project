
class Conference:
    def __init__(self, server, uuid, conference_name):
        '''
        :param server: socket
        :param uuid: str
        :param conference_name: str
        '''
        self.server = server
        self.connected_clients = {} # http connection
        self.clients_num = 0
        self.connected_streams = {} # udp connection
        self.streams_num = 0
        self.conference_id = uuid
        self.conference_name = conference_name
        self.mode = Mode.P2P # default mode is P2P

    def from_query(query):
        '''
        create a new conference from the query
        :param query: dict
        :return: Conference
        '''
        return Conference(query['server'], query['uuid'], query['conference_name'])

    def add_client(self, client):
        '''
        add a client to the conference
        :param client: socket
        '''
        pass

    def remove_client(self, client):
        '''
        remove a client from the conference
        :param client: socket
        '''
        pass

    def upgrade(self, mode):
        '''
        upgrade the conference mode
        :param mode: Mode
        '''
        if (self.mode == mode):
            return
        elif (mode == Mode.C2S):
            # Todo: upgrade to C2S
            pass
        elif (mode == Mode.P2P):
            # Todo: upgrade to P2P
            pass

    def jsonify(self):
        '''
        return the conference information in json format
        :return: str
        '''
        return str(dict(
            conference_id=self.conference_id,
            conference_name=self.conference_name,
            connected_clients=dict(map(lambda x: (x[0], x[1].jsonify()), self.connected_clients.items())),
            clients_num=self.clients_num,
            streams_num=self.streams_num,
            mode=self.mode
        ))
        pass