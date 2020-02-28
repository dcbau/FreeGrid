import sounddevice as sd
from scipy.signal import chirp
import matplotlib.pyplot as mplot
import matplotlib
import scipy.io.wavfile as wave
from numpy.fft import fft, ifft
import numpy as np
import time



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
        f_start = 20
        f_end = 20000

        # make sweep
        t_sweep = np.linspace(0, sweeplength_sec, sweeplength_sec * fs)
        sweep = amplitude_lin * chirp(t_sweep, f0=f_start, t1=sweeplength_sec, f1=f_end, method='logarithmic', phi=90)

        silence = np.zeros(fs * silencelength_sec)

        self.excitation = np.append(sweep, silence)
        self.excitation = np.array([self.excitation, self.excitation])  # make stereo, for out channels 1 & 2
        self.excitation = np.transpose(self.excitation).astype(np.float32)

        self.fs = fs

        self.measurement_count = 0

        self.recorded_sweep_l = []
        self.recorded_sweep_r = []
        self.feedback_loop = []
        self.recorded_ir = []
        self.recorded_sr = []
        self.recorded_nch = []

    def single_measurement(self):

        time.sleep(0.5)

        #should be adaptive!
        available_in_channels = 2

        # do measurement

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
            recorded = sd.playrec(self.excitation, self.fs, channels=3)
            sd.wait()

            self.recorded_sweep_l = recorded[:, 0]
            self.recorded_sweep_r = recorded[:, 1]
            self.feedback_loop = recorded[:, 2]







    def save_single_measurement(self, valid, _az, _el, _r):

        if valid:

            ir_l = ifft(fft(self.recorded_sweep_l) / fft(self.feedback_loop))
            ir_r = ifft(fft(self.recorded_sweep_r) / fft(self.feedback_loop))

            ir = np.array([ir_l, ir_r])
            print('Saving an array')
            print( np.shape(ir))

            #filename = "ir_" + str(self.measurement_count) + "_" + str(int(round(_az))) + "_" + "_" + str(int(round(_el))) + ".wav"
            #self.measurement_count += 1



        self.recorded_ir = []
        self.recorded_sr = []
        self.recorded_nch = []
        self.recorded_sweep = []
        self.feedback_loop = []
