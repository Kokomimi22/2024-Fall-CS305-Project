from enum import Enum
from typing import *
HELP = 'Create         : create an conference\n' \
       'Join [conf_id]: join a conference with conference ID\n' \
       'Quit           : quit an on-going conference\n' \
       'Cancel         : cancel your on-going conference (only the manager)\n' \
       'On [datatype(screen, video, audio)]  : turn on the data type\n' \
       'Off [datatype(video, audio)] : turn off the data type\n' \
       'Text [message] : send a text message\n' \
       'Get_conferences: get the list of all conferences\n' \
       'Switch_video_mode: switch the video mode\n' \
       'Logout         : logout\n' \
       'Exit           : exit the program\n' \
       'Help           : show help information\n'

SERVER_IP = '10.26.170.123'
USE_GUI = True
MAIN_SERVER_PORT = 8888
TIMEOUT_SERVER = 5
LOG_INTERVAL = 2
CONTROL_LINE_BUFFER = 1024
DATA_LINE_BUFFER = 4096
USER_INFO_FILE = 'user_info.json'
CONFIG_INFO_FILE = 'config/appconfig.json'
CHUNK = 4096  # Audio chunk size
CHANNELS = 1  # Channels for audio capture
RATE = 44100  # Sampling rate for audio capture
SAMPLE_SIZE = 16  # Sample size for audio capture
CODE_C = 'audio/pcm'  # Codec for audio capture
SUCCESSFUL = True
FAILED = False
camera_width, camera_height = 960, 540   # resolution for camera and screen capture
VIDEO_CHUNK_SIZE = 8192  # UDP
view_width, view_height = 960, 540  # resolution for video display


class MessageType(Enum):
    GET_CONFERENCES = 'get_conferences'
    LOGIN = 'login'
    LOGOUT = 'logout'
    CREATE = 'create_conference'
    JOIN = 'join_conference'
    QUIT = 'quit_conference'
    CANCEL = 'cancel_conference'
    REGISTER = 'register'
    INIT = 'init_conference'
    TEXT_MESSAGE = 'text_message'
    SWITCH_TO_P2P = 'switch_to_p2p'
    SWITCH_TO_CS = 'switch_to_cs'
    P2P_INFOS_NOTIFICATION = 'p2p_infos_notification'

class Status(Enum):
    SUCCESS = True
    FAILED = False

class DistributeProtocol(Enum):
    PEER_TO_PEER = 'peer_to_peer'
    CLIENT_SERVER = 'client_server'