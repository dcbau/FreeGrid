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

        devices = sd.query_devices()
        print(devices)
        print(sd.default.device)

        fs = 48000

        # define sweep parameters
        sweeplength_sec = 3
        silencelength_sec = 1
        amplitude_db = -20
        amplitude_lin = 10 ** (amplitude_db / 20)
        f_start = 100
        f_end = 20000

        # make sweep
        t_sweep = np.linspace(0, sweeplength_sec, sweeplength_sec * fs)
        sweep = amplitude_lin * chirp(t_sweep, f0=f_start, t1=sweeplength_sec, f1=f_end, method='logarithmic', phi=90)

        silence = np.zeros(fs * silencelength_sec)

        self.excitation = np.append(sweep, silence)
        self.excitation = np.array([self.excitation, self.excitation])  # make stereo, for out channels 1 & 2
        self.excitation = np.transpose(self.excitation).astype(np.float32)

        self.fs = fs

        self.recorded_sweep_l = []
        self.recorded_sweep_r = []
        self.feedback_loop = []
        self.ir_l = []
        self.ir_r = []

    def single_measurement(self):

        self.recorded_sweep_l = []
        self.recorded_sweep_r = []
        self.feedback_loop = []
        self.ir_l = []
        self.ir_r = []

        time.sleep(2)

        available_in_channels = sd.query_devices(sd.default.device[0])['max_input_channels']

        # do measurement

        if(available_in_channels == 1):
            # ch1 = left
            # ch2 = right
            recorded = sd.playrec(self.excitation, self.fs, channels=1)
            sd.wait()

            self.recorded_sweep_l = recorded[:, 0]
            self.recorded_sweep_r = recorded[:, 0]
            self.feedback_loop = self.excitation[:, 0]

        if(available_in_channels == 2):

            # ch1 = left
            # ch2 = right
            recorded = sd.playrec(self.excitation, self.fs, channels=2)
            sd.wait()

            self.recorded_sweep_l = recorded[:, 0]
            self.recorded_sweep_r = recorded[:, 1]
            self.feedback_loop = self.excitation[:, 0]

        elif(available_in_channels > 2):

            # ch1 = left
            # ch2 = right
            # ch3 = feedback loop
            recorded = sd.playrec(self.excitation, self.fs, channels=1)
            sd.wait()

            self.recorded_sweep_l = recorded[:, 0]
            self.recorded_sweep_r = recorded[:, 1]
            self.feedback_loop = recorded[:, 2]

        # make IR
        self.ir_l = deconv(self.feedback_loop, self.recorded_sweep_l)
        self.ir_r = deconv(self.feedback_loop, self.recorded_sweep_r)


    def get_recordings(self):
        return [self.recorded_sweep_l, self.recorded_sweep_r, self.feedback_loop]

    def get_irs(self):
        try:
            return [self.ir_l, self.ir_r]
        except:
            return
