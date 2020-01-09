import sounddevice as sd
import soundfile as sf
import time
import scipy.io as scio
import numpy as np
import queue

import wave


class Measurement():

    def __init__(self):

        self.queue = queue.Queue()
        device_info = sd.query_devices(sd.default.device, 'input')
        # soundfile expects an int, sounddevice provides a float:
        self.samplerate = int(device_info['default_samplerate'])

    def shutdown(self):
        print("Shutdown Audio")

    def callback(self, indata, outdata, frames, time, status):
        if status:
            print(status)
        outdata[:] = indata


    def single_measurement(self, fname = "/Users/davidbau/audio_test_files/drums.wav"):

        # print("Record with ", sd.default.device)
        # file = "/Users/davidbau/audio_test_files/drums.wav"
        # data, fs = sf.read(file = file)
        # sd.play(data, fs, device=0)
        # sd.wait()
        # duration = 1
        # myrecording = sd.rec(int(duration*self.samplerate), samplerate=self.samplerate, channels=1, device=3)
        # sd.wait()
        #
        # filename = 'test_file_2.mat'
        # scio.savemat(filename, {'recorded_signal': myrecording, 'fs': self.samplerate})

        with sd.Stream(channels = 1, callback=self.callback):
            sd.sleep(int(5*1000))




