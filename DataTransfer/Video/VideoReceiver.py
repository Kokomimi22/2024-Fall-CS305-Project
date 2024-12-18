import math
import queue
import socket
import struct

import av
import cv2

from config import *
from util import overlay_camera_images


class VideoReceiver:
    def __init__(self, socket_connection: socket.socket):
        self._display_thread = None
        self.sock = socket_connection
        self.sock.setblocking(False)
        self.buffers = {}
        self.expected_sequences = {}
        self.received_chunks = {}
        self.frames = {}
        self._running = False
        # 用于存储解码器的字典
        self.decoders: Dict[str,  av.codec.context.CodecContext] = {}
        self.gridimage_queue = queue.Queue()  #线程安全队列

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
            'refcounted_frames': '1'  # 使用引用计数帧
        }
        self.decoders[client_id] = codec

    def start(self):
        self._running = True
        while self._running:
            try:
                data, _ = self.sock.recvfrom(65536)
                if data == b'Cancelled':
                    break
            except BlockingIOError:
                continue
            except ConnectionResetError:
                print("Connection reset by the server")
                break

            client_id, data_len, sequence_number, chunk_data = self._unpack_data(data)

            if chunk_data == b'TERMINATE':
                self.remove_client(client_id)
                continue

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
                        img = frame.to_ndarray(format='bgr24')
                        self.frames[client_id] = img

                        # 显示所有摄像头画面
                        camera_images = list(self.frames.values())
                        if camera_images:
                            grid_size = int(math.ceil(math.sqrt(len(camera_images))))
                            grid_image = overlay_camera_images(camera_images, (grid_size, grid_size))
                            self.gridimage_queue.put(grid_image)
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
        if not self.frames:
            cv2.destroyAllWindows()

    def output_image(self):
        if not self.gridimage_queue.empty():
            return self.gridimage_queue.get()

    def clear(self):
        self.decoders.clear()
        self.buffers.clear()
        self.expected_sequences.clear()
        self.received_chunks.clear()
        self.frames.clear()

    def terminate(self):
        if not self._running:
            return
        self._running = False
        self.clear()
