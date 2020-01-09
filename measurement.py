import pyaudio
import wave



class Measurement():

    def __init__(self):
        self.p = pyaudio.PyAudio()
        info = self.p.get_host_api_info_by_index(0)
        self.host_api = info.get('name')
        numdevices = info.get('deviceCount')
        print("\nAvailable Devices:")
        self.input_devices = []
        self.output_devices = []
        for i in range(0, numdevices):

            dev = {
                "name": self.p.get_device_info_by_host_api_device_index(0, i).get('name'),
                "numInputChannels": self.p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels'),
                "numOutputChannels": self.p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels'),
                "index": i
            }

            if dev["numInputChannels"] > 0:
                self.input_devices.append(dev)
                print("Input Device id ", i, " - ", dev['name'])

            if dev["numOutputChannels"] > 0:
                self.output_devices.append(dev)
                print("Output Device id ", i, " - ", dev['name'])


        self.current_output_device = self.p.get_default_output_device_info()["index"]
        self.current_input_device = self.p.get_default_input_device_info()["index"]

        print("Default Output Device: ", self.current_output_device)

        self.measurement_count = 0
        self.recorded_sweep = []
        self.recorded_sr = []
        self.recorded_nch = []


    def single_measurement(self, fname = "/Users/davidbau/audio_test_files/sweep_50-22k.wav"):
        wf = wave.open(fname, 'rb')
        chunk = 1024

        n_chn_in, n_chn_out = self.get_available_channels_in_out()

        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        output_device_index=self.current_output_device)

        data = wf.readframes(chunk)

        stream_rec = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=n_chn_in,
                            rate=wf.getframerate(),
                            input=True,
                            input_device_index=self.current_input_device)

        print("Start Playback")
        index = 0
        frames = []
        while index < wf.getnframes():
            stream.write(data)
            data = wf.readframes(chunk)
            index += chunk
            frames.append(stream_rec.read(chunk))

        print("Playback finished")

        stream_rec.close()
        stream.close()
        p.terminate()

        self.recorded_sweep = frames
        self.recorded_sr = wf.getframerate()
        self.recorded_nch = n_chn_in




    def save_single_measurement(self, valid, _az, _el, _r):

        if valid:

            filename = "recorded_sweep_" + str(self.measurement_count) + "_" + str(_az) + "_" + "_" + str(_r) + ".wav"
            self.measurement_count += 1
            wavefile = wave.open(filename, 'wb')
            wavefile.setnchannels(self.recorded_nch)
            p = pyaudio.PyAudio()
            wavefile.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wavefile.setframerate(self.recorded_sr)
            wavefile.writeframes(b''.join(self.recorded_sweep))
            wavefile.close()

        self.recorded_ir = []
        self.recorded_sr = []
        self.recorded_nch = []

    def get_input_devices(self):
        return self.input_devices

    def get_output_devices(self):
        return self.output_devices

    def set_output_device_by_name(self, name):
        for dev in self.output_devices:
            if (name == dev['name']):
                self.current_output_device = dev['index']
                print("New Output: ", self.current_output_device, " (", name, ")")

    def set_input_device_by_name(self, name):
        for dev in self.input_devices:
            if (name == dev['name']):
                self.current_input_device = dev['index']
                print("New Input: ", self.current_input_device, " (", name, ")")


    # def get_current_output_device(self):
    #     return self.p.get_device_info_by_host_api_device_index(0, self.current_output_device).get('name')
    #
    # def get_current_input_device(self):
    #     return self.p.get_device_info_by_host_api_device_index(0, self.current_input_device).get('name')

    def set_input_channels(self):
       self.output_stream_info = pyaudio.PaMacCoreStreamInfo(None, )

    def get_available_channels_in_out(self):

        for dev in self.input_devices:
            if (self.current_input_device == dev['index']):
                n_ch_in = dev['numInputChannels']
        for dev in self.output_devices:
            if (self.current_output_device == dev['index']):
                n_ch_out = dev['numOutputChannels']

        print("N In Channels: ", n_ch_in)
        return n_ch_in, n_ch_out