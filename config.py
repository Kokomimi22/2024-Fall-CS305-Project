from enum import Enum
from typing import *
HELP = 'Create         : create an conference\n' \
       'Join [conf_id]: join a conference with conference ID\n' \
       'Quit           : quit an on-going conference\n' \
       'Cancel         : cancel your on-going conference (only the manager)\n' \
       'On [datatype]  : turn on the data type\n\n' \

SERVER_IP = '127.0.0.1'
MAIN_SERVER_PORT = 8888
TIMEOUT_SERVER = 5
LOG_INTERVAL = 2
CONTROL_LINE_BUFFER = 1024
DATA_LINE_BUFFER = 4096
USER_INFO_FILE = 'user_info.json'
CHUNK = 4096  # Audio chunk size
CHANNELS = 1  # Channels for audio capture
RATE = 44100  # Sampling rate for audio capture
SAMPLE_SIZE = 16  # Sample size for audio capture
CODE_C = 'audio/pcm'  # Codec for audio capture
SUCCESSFUL = True
FAILED = False
camera_width, camera_height = 480, 480  # resolution for camera capture
VIDEO_CHUNK_SIZE = 20000  # UDP
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
class Status(Enum):
       SUCCESS = True
       FAILED = False