import io
import struct
import threading
import time

import av
import cv2

from config import *


class VideoSender:
    def __init__(self, camera, socket_connection, client_id=None, frame_rate=30):
        self.camera = camera
        self.client_id = client_id.encode('utf-8') if client_id else b''
        self.frame_rate = frame_rate
        self.sock = socket_connection
        self._running = False
        self._thread = None
        # 初始化编码器
        self.codec_context = self._create_codec_context()

    def _create_codec_context(self):

        # 创建内存缓冲区作为输出容器
        buffer = io.BytesIO()
        container = av.open(buffer, mode='w', format='h264')

        # 创建视频流
        stream = container.add_stream('h264', rate=self.frame_rate)
        stream.width = camera_width
        stream.height = camera_height
        stream.pix_fmt = 'yuv420p'

        # 设置编码器参数
        stream.options = {
            'preset': 'ultrafast',  # 最快的编码速度
            'tune': 'zerolatency',  # 最低延迟
            'x264-params': 'nal-hrd=cbr:force-cfr=1',  # 固定比特率
            'crf': '23',  # 压缩质量（0-51，23为默认值）
            'profile': 'baseline',  # 基准配置，更好的兼容性
            'level': '3.0'
        }
        return stream

    def _process_data(self):
        client_id_len = len(self.client_id)
        while self._running:
            start_time = time.time()
            ret, frame = self.camera.get_frame()
            if not ret:
                continue
            # 调整帧的分辨率
            frame = cv2.resize(frame, (camera_width, camera_height))
            # 转换为PyAV帧格式
            av_frame = av.VideoFrame.from_ndarray(frame, format='bgr24')

            try:
                # 编码帧
                # encode似乎来自C扩展，PyCharm似乎无法识别，别在意这个警告
                packets = self.codec_context.encode(av_frame)
                # 一个packets里只有一帧数据
                for packet in packets:
                    # 获取编码后的数据
                    encoded_data = bytes(packet)
                    data_len = len(encoded_data)
                    # 分块发送数据
                    num_chunks = (data_len // VIDEO_CHUNK_SIZE) + 1
                    sequence_number = 0

                    for i in range(num_chunks):
                        chunk = encoded_data[i * VIDEO_CHUNK_SIZE: (i + 1) * VIDEO_CHUNK_SIZE]
                        packet = (struct.pack("I", client_id_len) +
                                  self.client_id +
                                  struct.pack("Q", data_len) +
                                  struct.pack("I", sequence_number) +
                                  chunk)
                        self.sock.send(packet)
                        sequence_number += 1

            except Exception as e:
                print(f"Encoding error: {e}")
                continue
            elapse_time = time.time() - start_time
            # 控制帧率
            time.sleep(max(1.0 / self.frame_rate - elapse_time, 0))

    def start(self):
        if self._running:
            raise RuntimeError("VideoSender is already running")
        self._running = True
        self._thread = threading.Thread(target=self._process_data)
        self._thread.start()

    def stop(self):
        self._running = False
        self._thread.join()
        # 刷新编码器缓冲区
        if self.codec_context:
            try:
                packets = self.codec_context.encode(None)
                for packet in packets:
                    encoded_data = bytes(packet)
                    self.sock.send(encoded_data)
            except Exception as e:
                print(f"Error flushing encoder: {e}")
        self.camera.stop()

    def switch_mode(self):
        self.camera.switch_mode()

    def terminate(self, quitConf: bool=True):
        """
        终止视频发送, quitConf为False时就是关闭视频发送，为True时是直接退出会议
        :param quitConf: bool
        :return:
        """
        if not self._running:
            return None
        self.stop()
        terminate_signal = (struct.pack("I", len(self.client_id)) +
                            self.client_id +
                            struct.pack("Q", 0) +
                            struct.pack("I", 0) +
                            (b'TERMINATE' if quitConf else b'OFF'))
        try:
            self.sock.send(terminate_signal)
        except OSError:
            pass