import math
import socket
import struct
import threading
import time

import av
import cv2
from PIL import Image
from PyQt5.QtCore import pyqtSignal
from config import *
from util import overlay_camera_images


class VideoReceiver:
    def __init__(self, socket_connection: socket.socket, update_signal: pyqtSignal(Image.Image)):
        self.update_signal = update_signal
        self.sock = socket_connection
        self.sock.setblocking(False)
        self.buffers = {}
        self.expected_sequences = {}
        self.received_chunks = {}
        self.frames = {}
        self._running = False
        self._thread = None
        self.timeout = 5  # 超时时间
        self.time_record = {} # 超时删除
        # 用于存储解码器的字典
        self.decoders: Dict[str,  av.codec.context.CodecContext] = {}

    @staticmethod
    def _unpack_data(data):
        offset = 0
        client_id_len = struct.unpack_from("I", data, offset)[0]
        offset += struct.calcsize("I")
        client_id = data[offset:offset + client_id_len].decode('utf-8')
        offset += client_id_len
        data_len = struct.unpack_from("Q", data, offset)[0]
        offset += struct.calcsize("Q")
        sequence_number = struct.unpack_from("I", data, offset)[0]
        offset += struct.calcsize("I")
        chunk_data = data[offset:]
        return client_id, data_len, sequence_number, chunk_data

    def _create_decoder(self, client_id):
        # 为每个客户端创建解码器
        codec = av.CodecContext.create('h264', 'r')
        # 设置解码器参数
        codec.options = {
            'threads': '4',  # 使用多线程解码
            'refcounted_frames': '1',  # 使用引用计数帧
            'flags': 'low_delay',  # 降低延迟
            'flags2': 'fast'  # 使用快速解码
        }
        self.decoders[client_id] = codec

    def _check_timeouts(self):
        current_time = time.time()
        for client_id in list(self.time_record.keys()):
            if current_time - self.time_record[client_id] > self.timeout:
                print(f"Client {client_id} timed out")
                self.remove_client(client_id)

    def _process_data(self):
        while self._running:
            try:
                data, _ = self.sock.recvfrom(65536)
                if not data or data == b'Cancelled':
                    break
            except BlockingIOError:
                self._check_timeouts()
                time.sleep(0.005)
                continue
            except OSError:
                break
            self._check_timeouts()
            client_id, data_len, sequence_number, chunk_data = self._unpack_data(data)

            # 超时删除
            self.time_record[client_id] = time.time()

            # 初始化新客户端
            if client_id not in self.expected_sequences:
                self.expected_sequences[client_id] = 0
                self.received_chunks[client_id] = {}
                self.buffers[client_id] = b''
                self._create_decoder(client_id)

            self.received_chunks[client_id][sequence_number] = chunk_data
            # 按序处理数据块
            while self.expected_sequences[client_id] in self.received_chunks[client_id]:
                self.buffers[client_id] += self.received_chunks[client_id].pop(
                    self.expected_sequences[client_id]
                )
                self.expected_sequences[client_id] += 1

            if len(self.buffers[client_id]) < data_len:
                continue

            try:
                # 解码视频帧
                decoder = self.decoders[client_id]
                packets = decoder.parse(self.buffers[client_id])
                for packet in packets:
                    # decode方法来自C扩展，PyCharm有警告但没影响
                    frames = decoder.decode(packet)
                    for frame in frames:
                        # 转换为numpy数组
                        img = frame.to_ndarray(format='rgb24')
                        self.frames[client_id] = img

                        # 显示所有摄像头画面
                        camera_images = list(self.frames.values())
                        if camera_images:
                            grid_size = int(math.ceil(math.sqrt(len(camera_images))))
                            grid_image = overlay_camera_images(camera_images, (grid_size, grid_size))
                            if USE_GUI:
                                grid_image_pil = Image.fromarray(grid_image)
                                self.update_signal.emit(grid_image_pil)
                            else:
                                cv2.imshow('Video Grid', grid_image)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                self._running = False
                                break
            except Exception as e:
                print(f"Error decoding frame: {e}")

            # 清理缓冲区
            self.buffers[client_id] = b''
            self.expected_sequences[client_id] = 0

    def remove_client(self, client_id):
        self.decoders.pop(client_id, None)
        self.buffers.pop(client_id, None)
        self.expected_sequences.pop(client_id, None)
        self.received_chunks.pop(client_id, None)
        self.frames.pop(client_id, None)
        self.time_record.pop(client_id, None)
        #显示所有摄像头画面
        if USE_GUI:
            camera_images = list(self.frames.values())
            if camera_images:
                grid_size = int(math.ceil(math.sqrt(len(camera_images))))
                grid_image = overlay_camera_images(camera_images, (grid_size, grid_size))
                grid_image_pil = Image.fromarray(grid_image)
                self.update_signal.emit(grid_image_pil)
            else:
                self.update_signal.emit(Image.new('RGB', (640, 480)))
                print("No camera images to display")
        else:
            if not self.frames:
                print("No more frames to display")
                cv2.destroyAllWindows()

    def clear(self):
        self.decoders.clear()
        self.buffers.clear()
        self.expected_sequences.clear()
        self.received_chunks.clear()
        self.frames.clear()
        self.time_record.clear()

    def start(self):
        if self._running:
            raise RuntimeError("VideoReceiver is already running")
        self._running = True
        self._thread = threading.Thread(target=self._process_data)
        self._thread.start()

    def terminate(self):
        if not self._running:
            return
        self._running = False
        self._thread.join()
        cv2.destroyAllWindows()
        self.clear()
