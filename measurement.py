import sounddevice as sd
from scipy.signal import chirp
import matplotlib.pyplot as mplot
import matplotlib
import scipy.io.wavfile as wave
from numpy.fft import fft, ifft
import numpy as np
import time


def deconv(x, y):

    # zero padding
    input_length = np.size(y)
    n = np.ceil(np.log2(input_length)) + 1
    padded_length = int(pow(2, n))
    num_zeros_to_append = padded_length - input_length

    x = np.pad(x, (0, num_zeros_to_append))
    y = np.pad(y, (0, num_zeros_to_append))

    # deconvolution
    h = ifft(fft(y) / fft(x)).real
    # truncate and window
    h = h[0:input_length]

    # squared cosine fade
    fadeout_length = 2000
    fade_tmp = np.cos(np.linspace(0, np.pi / 2, fadeout_length)) ** 2
    window = np.ones(np.size(h))
    window[np.size(window) - fadeout_length: np.size(window)] = fade_tmp
    h = h * window

    return h


class Measurement():

    def __init__(self):

        #devices = sd.query_devices()
        #print(devices)
        #print(sd.default.device)

        self.get_names_of_defualt_devices()

        self.fs = sd.default.samplerate
        if self.fs is None:
            sd.default.samplerate = 48000
            self.fs = sd.default.samplerate


        print(f'Using Samplerate: {sd.default.samplerate}')

        # define sweep parameters
        sweeplength_sec = 3
        silencelength_sec = 1
        amplitude_db = -20
        f_start = 20
        f_end = 20000

        self.dummy_debugging = False

        #make sweep
        self.excitation = self.make_excitation_sweep(f_start=100, d_sweep_sec=2)
        self.excitation_3ch = self.make_excitation_sweep(num_channels=3, f_start=100, d_sweep_sec=2)
        self.excitation_hpc = self.make_excitation_sweep(d_sweep_sec=2)
        self.excitation_hpc_3ch = self.make_excitation_sweep(num_channels=3, d_sweep_sec=2)

        #read sound files
        self.sound_success_fs, self.sound_success = wave.read('Resources/soundfx_success.wav')
        self.sound_failed_fs, self.sound_failed = wave.read('Resources/soundfx_failed.wav')


        self.sound_failed = self.sound_failed * 0.05 / 32768
        self.sound_success = self.sound_success * 0.05 / 32768



        self.recorded_sweep_l = []
        self.recorded_sweep_r = []
        self.feedback_loop = []
        self.ir_l = []
        self.ir_r = []

    def make_excitation_sweep(self, num_channels=2, d_sweep_sec=3, d_post_silence_sec=1, f_start=20, f_end=20000, amp_db=-20):

        amplitude_lin = 10 ** (amp_db / 20)

        if self.dummy_debugging:
            d_sweep_sec = 0.01

        # make sweep
        t_sweep = np.linspace(0, d_sweep_sec, d_sweep_sec * self.fs)
        sweep = amplitude_lin * chirp(t_sweep, f0=f_start, t1=d_sweep_sec, f1=f_end, method='logarithmic', phi=90)

        silence = np.zeros(self.fs * d_post_silence_sec)
        if self.dummy_debugging:
            silence = np.zeros(2000)

        excitation = np.append(sweep, silence)

        excitation = np.tile(excitation, (num_channels, 1))  # make stereo or more, for out channels 1 & 2
        excitation = np.transpose(excitation).astype(np.float32)

        return excitation




    def play_sound(self, success):
        if success:
            sd.play(self.sound_success, self.sound_success_fs)
        else:
            sd.play(self.sound_failed, self.sound_failed_fs)
        sd.wait()

    def interrupt_measurement(self):
        sd.stop()

    def single_measurement(self, type=None):

        self.recorded_sweep_l = []
        self.recorded_sweep_r = []
        self.feedback_loop = []
        self.ir_l = []
        self.ir_r = []

        excitation = self.excitation
        excitation_3ch = self.excitation_3ch

        if type is 'hpc':
            excitation = self.excitation_hpc
            excitation_3ch = self.excitation_hpc_3ch

        if not self.dummy_debugging:
            time.sleep(0.3)

        available_in_channels = sd.query_devices(sd.default.device[0])['max_input_channels']

        # do measurement
        if(available_in_channels == 1):
            # ch1 = left & right
            recorded = sd.playrec(excitation, self.fs, channels=1)
            sd.wait()

            self.recorded_sweep_l = recorded[:, 0]
            self.recorded_sweep_r = recorded[:, 0]
            self.feedback_loop = excitation[:, 0]

        elif(available_in_channels == 2):

            # ch1 = left
            # ch2 = right
            recorded = sd.playrec(excitation, self.fs, channels=2)
            sd.wait()

            self.recorded_sweep_l = recorded[:, 0]
            self.recorded_sweep_r = recorded[:, 1]
            self.feedback_loop = excitation[:, 0]

        elif(available_in_channels > 2):

            # ch1 = left
            # ch2 = right
            # ch3 = feedback loop
            recorded = sd.playrec(excitation_3ch, self.fs, channels=3)
            sd.wait()

            self.recorded_sweep_l = recorded[:, 0]
            self.recorded_sweep_r = recorded[:, 1]
            self.feedback_loop = recorded[:, 2]


        # make IR
        self.ir_l = deconv(self.feedback_loop, self.recorded_sweep_l)
        self.ir_r = deconv(self.feedback_loop, self.recorded_sweep_r)


    def get_names_of_defualt_devices(self):
        input_dev = sd.query_devices(sd.default.device[0])
        output_dev = sd.query_devices(sd.default.device[1])

        out_excitation = output_dev['name'] + ", Ch1"
        num_in_ch = input_dev['max_input_channels']
        num_out_ch = output_dev['max_output_channels']

        device_strings = {
            "out_excitation": "Unavailable",
            "out_excitation_2": "Unavailable",
            "out_feedback": "Unavailable/Disabled",
            "in_left": "Unavailable",
            "in_right": "Unavailable",
            "in_feedback": "Unavailable/Disabled"
        }
        if num_out_ch > 0:
            device_strings["out_excitation"] = output_dev['name'] + ", Ch1"
        if num_out_ch > 1:
            device_strings["out_excitation_2"] = output_dev['name'] + ", Ch2"
        if num_in_ch > 0:
            device_strings["in_left"] = input_dev['name'] + ", Ch1"
        if num_in_ch > 1:
            device_strings["in_right"] = input_dev['name'] + ", Ch2"
        if num_in_ch > 2 and num_out_ch > 2:
            device_strings["in_feedback"] = input_dev['name'] + ", Ch3"
            device_strings["out_feedback"] = output_dev['name'] + ", Ch3"

        return device_strings


    def get_recordings(self):
        return [self.recorded_sweep_l, self.recorded_sweep_r, self.feedback_loop]

    def get_irs(self):
        try:
            return [self.ir_l, self.ir_r]
        except:
            return
