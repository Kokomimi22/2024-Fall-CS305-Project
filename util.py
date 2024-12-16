"""
Simple util implementation for video conference
Including data capture, image compression and image overlap
Note that you can use your own implementation as well :)
"""
import socket
from io import BytesIO

import pyaudio
import cv2
import pyautogui
import numpy as np
from PIL import Image, ImageGrab
from PyQt5.QtMultimedia import QCameraInfo, QAudioDeviceInfo, QAudio, QCamera, QCameraImageCapture, QAudioInput, \
    QAudioFormat
from deprecated.sphinx import deprecated

from config import *
import uuid

# audio setting
FORMAT = pyaudio.paInt16
QAUDIO_FORMAT = QAudioFormat()
QAUDIO_FORMAT.setSampleRate(RATE)
QAUDIO_FORMAT.setChannelCount(CHANNELS)
QAUDIO_FORMAT.setSampleSize(SAMPLE_SIZE)
QAUDIO_FORMAT.setCodec(CODE_C)
QAUDIO_FORMAT.setByteOrder(QAudioFormat.LittleEndian)
QAUDIO_FORMAT.setSampleType(QAudioFormat.SignedInt)

audio = pyaudio.PyAudio()

try:
    streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
except Exception as e:
    print(e)
    streamin = None
    streamout = None

# print warning if no available camera
cap = cv2.VideoCapture(0)
if cap.isOpened():
    can_capture_camera = True
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
else:
    can_capture_camera = False

my_screen_size = pyautogui.size()


def get_port() -> int:
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def resize_image_to_fit_screen(image, my_screen_size):
    screen_width, screen_height = my_screen_size

    original_width, original_height = image.size

    aspect_ratio = original_width / original_height

    if screen_width / screen_height > aspect_ratio:
        # resize according to height
        new_height = screen_height
        new_width = int(new_height * aspect_ratio)
    else:
        # resize according to width
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)

    # resize the image
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)

    return resized_image


def overlay_camera_images(camera_images: List[np.array], grid_size=(2, 2)):
    """
    Overlay multiple camera images into a grid.

    :param camera_images: list of np.array, list of camera images
    :param grid_size: tuple, grid size (rows, columns)
    :return: np.array, combined image in numpy array format
    """
    if not camera_images:
        raise ValueError("No camera images to overlay")

    # Determine the size of each cell in the grid
    cell_height, cell_width, _ = camera_images[0].shape

    # Create a blank image for the grid
    grid_height = cell_height * grid_size[0]
    grid_width = cell_width * grid_size[1]
    grid_image = np.zeros((grid_height, grid_width, 3), dtype=np.uint8)

    # Paste each camera image into the grid
    for idx, camera_image in enumerate(camera_images):
        row = idx // grid_size[1]
        col = idx % grid_size[1]
        y = row * cell_height
        x = col * cell_width
        grid_image[y:y + cell_height, x:x + cell_width] = camera_image

    return grid_image

def capture_screen():
    # capture screen with the resolution of display
    # img = pyautogui.screenshot()
    img = ImageGrab.grab()
    return img


def capture_camera()->np.array:
    # capture frame of camera
    ret, frame = cap.read()
    if not ret:
        raise Exception('Fail to capture frame from camera')
    return ret, frame

def release_camera():
    global cap
    if cap.isOpened():
        cap.release()
    # Reinitialize the video capture object
    cap = cv2.VideoCapture(0)

def qcapture_audio(audioinput: QAudioInput):
    # capture frame of camera
    if audioinput is None:
        raise Exception('Audio is not available')
    elif not audioinput.isAvailable():
        raise Exception('Audio is not available')
    elif not audioinput.status() == QAudio.ActiveStatus:
        raise Exception('Audio is not active')
    else:
        pass
    raise NotImplementedError('qcapture_audio is not implemented yet')

def qcapture_camera(camera: QCamera):
    img = None
    def handle_image_capture(data, image):
        image
    # capture frame of camera
    if camera is None:
        raise Exception('Camera is not available')
    elif not camera.isAvailable():
        raise Exception('Camera is not available')

    else:
        image_capture = QCameraImageCapture(camera)
        image_capture.setCaptureDestination(QCameraImageCapture.CaptureToBuffer)
        image_capture.imageCaptured.connect(handle_image_capture)
        return img




def capture_voice():
    raise RuntimeError("This method can't be called currently")

@deprecated(version='1.0', reason="This method is deprecated")
def compress_image(image: Image, format='JPEG', quality=85):
    """
    compress image and output Bytes

    :param image: PIL.Image, input image
    :param format: str, output format ('JPEG', 'PNG', 'WEBP', ...)
    :param quality: int, compress quality (0-100), 85 default
    :return: bytes, compressed image data
    """
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format=format, quality=quality, optimize=True)
    img_byte_arr = img_byte_arr.getvalue()

    return img_byte_arr

@deprecated(version='1.0', reason="This method is deprecated")
def decompress_image(image_bytes):
    """
    decompress bytes to PIL.Image
    :param image_bytes: bytes, compressed data
    :return: PIL.Image
    """
    img_byte_arr = BytesIO(image_bytes)
    image = Image.open(img_byte_arr)

    return image

def getVideoDevices():
    """
    get all video devices
    :return: list, list of video devices
    """
    return QCameraInfo.availableCameras()

def getAudioOutputDevices():
    """
    get all audio devices
    :return: list, list of audio devices
    """
    devices = []
    device_name = []
    for device in QAudioDeviceInfo.availableDevices(QAudio.AudioOutput):
        if device.deviceName() not in device_name:
            devices.append(device)
            device_name.append(device.deviceName())
    return devices

def getAudioInputDevices():
    """
    get all audio devices
    :return: list, list of audio devices
    """
    devices = []
    device_name = []
    for device in QAudioDeviceInfo.availableDevices(QAudio.AudioInput):
        if device.deviceName() not in device_name:
            devices.append(device)
            device_name.append(device.deviceName())
    return devices

def audio_data_to_volume(data):
    """
    convert audio data to volume
    :param data: bytes, audio data
    :return: int, volume [0, 100]
    """
    # convert bytes to numpy array
    if not data:
        return 0
    data = np.frombuffer(data, dtype=np.int16)
    # calculate volume
    volume = np.sqrt(np.mean(data ** 2))
    volume = volume if volume < 100 else 100.0
    int16_max_value = np.iinfo(np.int16).max
    return int(volume)
        

### UUID module ###
class UUID:

    UUID_SIZE = 16

    def __init__(self):
        """
        default constructor, use uuid4
        """
        self.uuids = [] # list of uuids_hex

    def generate_uuid(self, length=UUID_SIZE):
        """
        generate an uuid in hex
        :param length: int, length of uuid in hex
        :return: str, uuid in hex
        """
        if length < 0:
            raise ValueError('length should be a positive integer')
        if length > 32:
            raise ValueError('length should be less than 32')
    
        _uuid_hex = uuid.uuid4().hex[:length]

        while _uuid_hex in self.uuids:
            _uuid_hex = uuid.uuid4().hex[:length]
        self.uuids.append(_uuid_hex)
        return _uuid_hex

    def remove_uuid(self, uuid_hex):
        """
        remove an uuid from the list
        :param uuid_hex: str, uuid in hex
        """
        if uuid_hex in self.uuids:
            self.uuids.remove(uuid_hex)
        else:
            raise ValueError('uuid not found')
    
    def get_uuids(self):
        """
        get all uuids
        :return: list, list of uuids in hex
        """
        return self.uuids

for device in getAudioOutputDevices():
    print(device.deviceName())
for device in getVideoDevices():
    print(device.description())