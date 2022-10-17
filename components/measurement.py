import sounddevice as sd
from scipy.signal import butter, sosfilt, resample_poly
import scipy.io.wavfile as wave
from components.dsp_helpers import make_excitation_sweep

import numpy as np
import time

import logging






class Measurement():

    def __init__(self):

        self.dummy_debugging = False

        if sd.default.samplerate is None:
            sd.default.samplerate = 48000

        '''Default parameters for the HRIR and CenterIR measurements'''
        self.sweep_parameters = {
            'sweeplength_sec': 1.0,
            'post_silence_sec': 0.5,
            'f_start': 100,
            'f_end': 22000,
            'amp_db': -20.0,
            'fade_out_samples': 200
        }

        # read sound files
        self.sound_success_fs, self.sound_success_singlechannel = wave.read('resources/soundfx_success.wav')
        self.sound_failed_fs, self.sound_failed_singlechannel = wave.read('resources/soundfx_failed.wav')

        # normalize and adjust level
        self.sound_failed_singlechannel = self.sound_failed_singlechannel * 0.05 / 32768
        self.sound_success_singlechannel = self.sound_success_singlechannel * 0.05 / 32768

        # default channels at startup
        self.channel_layout_input = [0, 1, -1]
        self.channel_layout_output = [0, 1, -1]
        self.num_input_channels_used = 2
        self.num_output_channels_used = 2
        self.feedback_loop_used = False

        self.sweep_mono = None
        self.sweep_hpc_mono = None
        self.excitation = None
        self.excitation_hpc = None
        self.sound_success = None
        self.sound_failed = None

        self.prepare_audio()


    def set_sweep_parameters(self, d_sweep_sec, d_post_silence_sec, f_start, f_end, amp_db, fade_out_samples):
        self.sweep_parameters['sweeplength_sec'] = d_sweep_sec
        self.sweep_parameters['post_silence_sec'] = d_post_silence_sec
        self.sweep_parameters['f_start'] = f_start
        self.sweep_parameters['f_end'] = f_end
        self.sweep_parameters['amp_db'] = amp_db
        self.sweep_parameters['fade_out_samples'] = fade_out_samples

        self.prepare_audio()

    def get_sweep_parameters(self):
        return self.sweep_parameters

    def get_samplerate(self):
        return sd.default.samplerate

    def set_channel_layout(self, in_channels, out_channels):
        """
        To be called when the audio channel layout has changed. Setting a channel to -1 disables it

        Parameters
        ----------
        in_channels : list of 3 ints with zero-indexed channel id, (-1 indicates disabled)
            1st entry: input channel left ear
            2nd entry: input channel right ear
            3rd entry: input channel feedback loop

        out_channels: list of 3 ints with zero-indexed channel id, (-1 indicates disabled)
            1st entry: output channel 1
            2nd entry: output channel 2
            3rd entry: output channel feedback loop

        """

        if out_channels[2] < 0 or in_channels[2] < 0:
            self.feedback_loop_used = False
            in_channels[2] = -1
            out_channels[2] = -1
        else:
            self.feedback_loop_used = True

        self.channel_layout_input = in_channels
        self.channel_layout_output = out_channels
        self.num_output_channels_used = max(out_channels) + 1
        self.num_input_channels_used = max(in_channels) + 1


        self.prepare_audio()

    def set_samplerate(self, fs=None):
        '''To be called when samplerate change occured.
        Parameters
        ----------
        fs :    New samplerate (int, optional) if not specified, that the samplerate has been set elsewhere via
                sonddevice.default.samplerate'''

        if fs is None:
            if sd.default.samplerate is None:
                sd.default.samplerate = 48000
        else:
            sd.default.samplerate = fs


        self.prepare_audio()

    def prepare_audio(self):
        # whenever something changes regarding the audio signals, recompute everything. Could be more efficient, but this
        # way the code remains simple
        fs = sd.default.samplerate

        # Make the sweep signals

        self.sweep_mono = make_excitation_sweep(fs=fs,
                                                d_sweep_sec=self.sweep_parameters['sweeplength_sec'],
                                                d_post_silence_sec=self.sweep_parameters['post_silence_sec'],
                                                f_start=self.sweep_parameters['f_start'],
                                                f_end=self.sweep_parameters['f_end'],
                                                amp_db=self.sweep_parameters['amp_db'],
                                                fade_out_samples=self.sweep_parameters['fade_out_samples'])

        if self.dummy_debugging:
            self.sweep_mono = make_excitation_sweep(fs=fs, f_start=100, d_sweep_sec=0.01, d_post_silence_sec=0.01)

        self.sweep_hpc_mono = make_excitation_sweep(fs=fs, d_sweep_sec=2, f_start=10, f_end=22000)

        # Adjust samplerate on the audio files
        sound_success_src = resample_poly(self.sound_success_singlechannel, round(fs), self.sound_success_fs)
        sound_failed_src = resample_poly(self.sound_failed_singlechannel, round(fs), self.sound_failed_fs)


        # Since portaudio does not support the useage of individual channels, the channel assignment is "faked" by
        # creating a multichannel audio file for playrec() and only playing the sweep on the selected output channels.
        # On the other side, only the selected input channels are used from the recorded multichannel wave file
        out_channels = self.channel_layout_output

        if not self.feedback_loop_used:
            out_channels = out_channels[0:2]


        # make multichannel audiofile and assign the sweep to designated channels
        self.excitation = np.zeros([np.size(self.sweep_mono, 0), self.num_output_channels_used])
        self.excitation[:, out_channels] = self.sweep_mono

        # same for HPC measurement
        self.excitation_hpc = np.zeros([np.size(self.sweep_hpc_mono, 0), self.num_output_channels_used])
        self.excitation_hpc[:, out_channels] = self.sweep_hpc_mono

        # also for the sound fx
        self.sound_success = np.zeros([np.size(sound_success_src, 0), self.num_output_channels_used])
        self.sound_success[:, out_channels[0:2]] = np.expand_dims(sound_success_src, axis=1)
        self.sound_failed = np.zeros([np.size(sound_failed_src, 0), self.num_output_channels_used])
        self.sound_failed[:, out_channels[0:2]] = np.expand_dims(sound_failed_src, axis=1)


    def play_sound(self, success):

        # little workaround of a problem with using ASIO from multiple threads
        # https://stackoverflow.com/questions/39858212/python-sounddevice-play-on-threads
        default_device = sd.query_devices(sd.default.device[0])
        default_api = sd.query_hostapis(default_device['hostapi'])
        if default_api['name'] == 'ASIO':
            sd._terminate()
            sd._initialize()

        if success:
            sd.play(self.sound_success)
        else:
            sd.play(self.sound_failed)
        sd.wait()

    def interrupt_measurement(self):
        logging.debug("Interrupt Measurement")
        sd.stop()

    def single_measurement(self, type=None):

        # little workaround of a problem with using ASIO from multiple threads
        # https://stackoverflow.com/questions/39858212/python-sounddevice-play-on-threads
        default_device = sd.query_devices(sd.default.device[0])
        default_api = sd.query_hostapis(default_device['hostapi'])
        if default_api['name'] == 'ASIO':
            sd._terminate()
            sd._initialize()


        print(f"Running type: {type}")
        if type == 'hpc':
            excitation = self.excitation_hpc
        else:
            excitation = self.excitation

        if not self.dummy_debugging:
            time.sleep(0.3)

        try:
            sd.check_input_settings(channels=self.num_input_channels_used)
            sd.check_output_settings(channels=self.num_output_channels_used)
        except:
            print("Audio hardware error! Too many channels or unsupported samplerate")
            return

        # do measurement
        recorded = sd.playrec(excitation, channels=self.num_input_channels_used)
        sd.wait()

        # get the recorded signals
        if self.channel_layout_input[0] >= 0:
            recorded_sweep_l = recorded[:, self.channel_layout_input[0]]
        else:
            recorded_sweep_l = np.zeros(np.size(recorded, 0))

        if self.channel_layout_input[1] >= 0:
            recorded_sweep_r = recorded[:, self.channel_layout_input[1]]
        else:
            recorded_sweep_r = np.zeros(np.size(recorded, 0))

        if self.feedback_loop_used:
            feedback_loop = recorded[:, self.channel_layout_input[2]]
            if abs(feedback_loop.max()) < 0.0001:
                feedback_loop = np.random.random_sample(feedback_loop.shape) * 0.000001  # to avoid zero-division errors
        else:
            # if no FB loop, copy from original excitation sweep
            if type == 'hpc':
                feedback_loop = self.sweep_hpc_mono[:, 0]
            else:
                feedback_loop = self.sweep_mono[:, 0]

        return recorded_sweep_l, recorded_sweep_r, feedback_loop


