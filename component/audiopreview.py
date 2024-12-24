# controller for audio preview card widget

from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtProperty, pyqtSlot, QIODevice
from PyQt5.QtMultimedia import QAudioOutput, QAudioInput
from qfluentwidgets import FluentIcon

from util import *

from view.testscreen import TestInterface

AudioPreviewCardView = TestInterface.SoundPreviewCard

class AudioPreview:
    def __init__(self, view: AudioPreviewCardView):
        # view initialization

        self.view = view

        # widget initialization
        self.visualizer = view.previewarea.progressSlider
        self.volume_control = view.previewarea.volumeButton
        self.play_control = view.previewarea.playButton
        self.volume_control.setVolume(100)

        # audio input/output initialization
        self.audio_input = None # type: QAudioInput
        self.audio_output = QAudioOutput(QAUDIO_FORMAT)
        self.io_device = None # type: QIODevice

        # status
        self.is_playing = False # is audio playing

        self.available_audio_input = {} # {sourceIndex: source}

        # signal connection
        self.play_control.clicked.connect(self.handle_toggle)
        self.view.selecsrcButton.clicked.connect(self.update_available_input)
        self.volume_control.volumeChanged.connect(self.handle_volume_change)
        self.volume_control.mutedChanged.connect(self.handle_mute_change)

        self.play_control.setDisabled(True) # disable play button until audio input is selected

        self.cur_volume = 50 # volume when output

    def handle_mute_change(self, muted):
        self.volume_control.setMuted(muted)
        if muted:
            self.handle_volume_change(0)
        else:
            self.handle_volume_change(self.cur_volume)

    def handle_toggle(self):
        self.play_control.setPlay(not self.is_playing)
        if not self.is_playing:
            self.start_audio()
        else:
            self.stop_audio()

    def start_audio(self):
        if not self.audio_input:
            return

        self.io_device = self.audio_input.start()
        self.audio_output.start(self.io_device)
        self.io_device.readyRead.connect(self.visualize_audio_data)
        self.is_playing = True

    def stop_audio(self):
        if not self.audio_input:
            return
        self.audio_input.stop()
        self.audio_output.stop()
        self.io_device.close()
        self.is_playing = False
        self.visualizer.setValue(0)


    def update_available_input(self): # trigger by select source button clicked
        available_audio_input_info = {i: source for i, source in enumerate(getAudioInputDevices())}
        self.view.selecsrcButton.clear()
        for i, source in available_audio_input_info.items():
            self.view.selecsrcButton.addItem(source.deviceName(), FluentIcon.MICROPHONE)
            self.available_audio_input[i] = QAudioInput(source, QAUDIO_FORMAT)

        if self.available_audio_input:
            self.play_control.setEnabled(True)
            self.handle_source_change(0)

    def handle_source_change(self, index): # trigger by combobox index changed
        assert index in self.available_audio_input
        if self.audio_input:
            self.audio_input.stop()
            self.audio_output.stop()
            self.audio_input.deleteLater()

        self.audio_input = self.available_audio_input[index]
        if self.is_playing:
            self.start_audio()

    def handle_volume_change(self, volume): # trigger by volume slider value changed
        self.cur_volume = volume
        self.audio_output.setVolume(volume / 100)

    def visualize_audio_data(self):
        if self.io_device:
            data = self.io_device.readAll()
            volume = audio_data_to_volume(data)
            scaler = self.cur_volume / 100
            self.visualizer.setValue(int(volume * scaler))




