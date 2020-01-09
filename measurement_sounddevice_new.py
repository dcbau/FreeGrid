import acoustics_hardware
import acoustics_hardware.serial
import time
import scipy.io as scio
import numpy as np
import sys
import sounddevice as sd
import soundfile as sf

import wave


class Measurement():

    def __init__(self):

        self.fs = 48000

        #devices = acoustics_hardware.devices.AudioDevice.get_devices()
        devices = sd.query_devices()
        self.input_devices = []
        self.output_devices = []

        i = 0
        for dev in devices:
            print(dev)
            dev["index"] = i
            if dev['max_input_channels'] > 0:
                self.input_devices.append(dev)
            if dev["max_output_channels"] > 0:
                self.output_devices.append(dev)
            i += 1

        self.current_input_device = []
        self.current_output_device = []
        print("Inputs: ", self.input_devices)
        print("Outputs: ", self.output_devices)
        self.set_input_device(self.input_devices[0])
        self.set_output_device(self.output_devices[0])


        #self.setupGenerator()

    def shutdown(self):
        print("Shutdown Audio")
        self.current_output_device.terminate()
        self.current_input_device.terminate()


    def single_measurement(self, fname = "/Users/davidbau/audio_test_files/drums.wav"):

        # print("Record with ", sd.default.device)

        # sd.wait()

        duration = 2

        device = acoustics_hardware.devices.AudioDevice("EDIROL UA-25")
        device.add_input(0)
        device.add_output(0)
        device.add_output(1)



        file = "/Users/davidbau/audio_test_files/drums.wav"
        data, fs = sf.read(file=file)
        #sd.play(data, fs, device=self.current_output_device)
        #sd.default.device = self.current_input_device

        myrecording = sd.playrec(data, samplerate=self.fs, channels=2, blocking=True)
        #myrecording = sd.rec(int(duration*self.fs), samplerate=self.fs, channels=1, device=self.current_input_device)

        #sd.wait()

        filename = 'test_file_2.mat'
        scio.savemat(filename, {'recorded_signal': myrecording, 'fs': self.fs})

        print("File successfully saved!")






    def setupGenerator(self):

        amplitude_db = -20
        self.sweep_duration = 3  # sec

        amplitude_lin = 10 ** (amplitude_db / 20)

        self.generator = acoustics_hardware.generators.SweepGenerator(device=self.current_output_device,
                                                                      start_frequency=50,
                                                                      stop_frequency=23e3,
                                                                      duration=self.sweep_duration,
                                                                      repetitions=1,
                                                                      amplitude=amplitude_lin)
    def get_input_devices(self):
        return self.input_devices

    def get_output_devices(self):
        return self.output_devices


    def set_input_device_by_name(self, name):
        for dev in self.input_devices:
            if(name == dev['name']):
                self.current_input_device = dev['index']
                print("New Input: ", self.current_input_device, " (", name, ")")

    def set_output_device_by_name(self, name):
        for dev in self.output_devices:
            if(name == dev['name']):
                self.current_output_device = dev['index']
                print("New Output: ", self.current_output_device, " (", name, ")")



    def set_output_device(self, dev):
        self.current_output_device = dev['index']


    def set_input_device(self, dev):
        self.current_input_device = dev['index']


    # def get_current_output_device(self):
    #     return self.p.get_device_info_by_host_api_device_index(0, self.current_output_device).get('name')
    #
    #
    # def get_current_input_device(self):
    #     return self.p.get_device_info_by_host_api_device_index(0, self.current_input_device).get('name')
    #
    # def set_input_channels(self):
    #    self.output_stream_info = pyaudio.PaMacCoreStreamInfo(None, )