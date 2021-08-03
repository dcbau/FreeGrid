import pyaudio
from scipy.signal import chirp, unit_impulse, butter, sosfilt, resample_poly
import scipy.io.wavfile as wave
from numpy.fft import fft, ifft, rfft, irfft
import numpy as np
import time
import threading

class AudioDeviceConfig():
    ## workaround class to provide settings like sounddevice´s default object

    def __init__(self, p):

        self.hostapi = p.get_default_host_api_info()['index']
        self.device = [p.get_default_input_device_info()['index'], p.get_default_output_device_info()['index']]
        self.samplerate = None
        self.frames_per_buffer = 1024

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

# deconvolution method similar to AKdeconv() from the AKtools matlab toolbox
def deconvolve(x, y, fs, max_inv_dyn=None, lowpass=None, highpass=None):
    input_length = np.size(x)
    n = np.ceil(np.log2(input_length)) + 1
    N_fft = int(pow(2, n))

    # transform
    X_f = rfft(x, N_fft)
    Y_f = rfft(y, N_fft)

    # invert input signal
    X_inv = 1 / X_f

    if max_inv_dyn is not None:
        # identify bins that exceed max inversion dynamic
        min_mag = np.min(np.abs(X_inv))
        mag_limit = min_mag * pow(10, np.abs(max_inv_dyn) / 20)
        ids_exceed = np.where(abs(X_inv) > mag_limit)

        # clip magnitude and leave phase untouched
        X_inv[ids_exceed] = mag_limit * np.exp(1j * np.angle(X_inv[ids_exceed]))

    if lowpass is not None or highpass is not None:
        # make fir filter by pushing a dirac through a butterworth SOS (multiple times)
        lp_filter = hp_filter = unit_impulse(N_fft)

        # lowpass
        if lowpass is not None:
            sos_lp = butter(lowpass[1], lowpass[0], 'lowpass', fs=fs, output='sos')
            for i in range(lowpass[2]):
                lp_filter = sosfilt(sos_lp, lp_filter)
        lp_filter = rfft(lp_filter)

        # highpass
        if highpass is not None:
            sos_hp = butter(highpass[1], highpass[0], 'highpass', fs=fs, output='sos')
            for i in range(highpass[2]):
                hp_filter = sosfilt(sos_hp, hp_filter)
        hp_filter = rfft(hp_filter)

        lp_hp_filter = hp_filter * lp_filter

        # apply filter
        X_inv = X_inv * lp_hp_filter

    # deconvolve
    H = Y_f * X_inv

    # backward transform
    h = irfft(H, N_fft)

    # truncate to original length
    h = h[:input_length]

    return h

def make_excitation_sweep(fs, num_channels=1, d_sweep_sec=3, d_post_silence_sec=1, f_start=20, f_end=20000, amp_db=-20, fade_out_samples=0):

    amplitude_lin = 10 ** (amp_db / 20)

    # make sweep
    t_sweep = np.linspace(0, d_sweep_sec, int(d_sweep_sec * fs))
    sweep = amplitude_lin * chirp(t_sweep, f0=f_start, t1=d_sweep_sec, f1=f_end, method='logarithmic', phi=90)

    # squared cosine fade
    fade_tmp = np.cos(np.linspace(0, np.pi / 2, fade_out_samples)) ** 2
    window = np.ones(np.size(sweep, 0))
    window[np.size(window) - fade_out_samples: np.size(window)] = fade_tmp
    sweep = sweep * window

    pre_silence = int(fs * 0.01) # 10msec post silence for safety while playback
    post_silence = int(fs * d_post_silence_sec)


    excitation = np.pad(sweep, (pre_silence, post_silence))

    excitation = np.tile(excitation, (num_channels, 1))  # make stereo or more, for out channels 1 & 2
    excitation = np.transpose(excitation).astype(np.float32)

    return excitation



class Measurement():

    def __init__(self):

        self.p = pyaudio.PyAudio()

        self.dummy_debugging = False

        self.sweep_parameters = {
            'sweeplength_sec': 3.0,
            'post_silence_sec': 1.5,
            'f_start': 100,
            'f_end': 22000,
            'amp_db': -20.0,
            'fade_out_samples': 200
        }

        #read sound files
        self.sound_success_fs, self.sound_success_singlechannel = wave.read('resources/soundfx_success.wav')
        self.sound_failed_fs, self.sound_failed_singlechannel = wave.read('resources/soundfx_failed.wav')

        # normalize and adjust level
        self.sound_failed_singlechannel = self.sound_failed_singlechannel * 0.05 / 32768
        self.sound_success_singlechannel = self.sound_success_singlechannel * 0.05 / 32768

        # default channels at startup
        self.channel_layout_input = [0, 1, -1]
        self.channel_layout_output = [0, 1, -1]
        self.num_input_channels_used = 0
        self.num_output_channels_used = 2
        self.feedback_loop_used = False

        self.sweep_mono = None
        self.sweep_hpc_mono = None
        self.excitation = None
        self.excitation_hpc = None
        self.sound_success = None
        self.sound_failed = None

        self.recorded_sweep_l = None
        self.recorded_sweep_r = None
        self.feedback_loop = None

        self.audio_settings = None
        self.set_audio_settings()

        self.audio_stream_out = None
        self.audio_stream_in = None


        self.playback_done = threading.Event()
        self.recording_buffer = None
        self.recording_done = threading.Event()
        self.measurement_type = 'hrir'
        self.measurement_error = False
        self.playback_index = None
        self.recording_index = None
        self.sample_is_playing = False
        self.sample_data = None

        #self.prepare_audio()


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
        return self.audio_settings.samplerate

    def set_audio_settings(self, audio_settings=None):

        if audio_settings is None:
            audio_settings=AudioDeviceConfig(self.p)

        if audio_settings.samplerate is None:
            audio_settings.samplerate = self.p.get_device_info_by_index(audio_settings.device[0])['defaultSampleRate']

        self.audio_settings = audio_settings

        self.prepare_audio()

    def get_pa_handler(self):
        return self.p

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


    def prepare_audio(self):
        # whenever something changes regarding the audio signals, recompute everything. Could be more efficient, but this
        # way the code remains simple

        # TODO: destroy stream here!!!!
        try:
            self.audio_stream_out.close()
            self.audio_stream_in.close()
        except:
            pass

        time.sleep(0.3)

        fs = int(self.audio_settings.samplerate)

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

        self.sweep_hpc_mono = make_excitation_sweep(fs=fs, d_sweep_sec=2)

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



        if self.num_input_channels_used > 0:
            self.audio_stream_in = self.p.open(format=pyaudio.paFloat32,
                                               channels=self.num_input_channels_used,
                                               rate=fs,
                                               input=True,
                                               stream_callback=self.audio_callback_input,
                                               input_device_index=self.audio_settings.device[0],
                                               frames_per_buffer=self.audio_settings.frames_per_buffer)
        if self.num_output_channels_used > 0:
            self.audio_stream_out = self.p.open(format=pyaudio.paFloat32,
                                               channels=self.num_output_channels_used,
                                               rate=fs,
                                               output=True,
                                               stream_callback=self.audio_callback_output,
                                               input_device_index=self.audio_settings.device[1],
                                               frames_per_buffer=self.audio_settings.frames_per_buffer)

        self.audio_stream_out.start_stream()



    def play_sound(self, success):
        pass
        # if success:
        #     sd.play(self.sound_success)
        # else:
        #     sd.play(self.sound_failed)
        # sd.wait()

    def interrupt_measurement(self):
        self.playback_index = None
        self.recording_index = None
        # sd.stop()

    def audio_callback_output(self, in_data, frame_count, time_info, status):


        interleaved = np.zeros(frame_count * self.num_output_channels_used)

        if self.playback_index is not None:
            if status != 0:
                self.measurement_error = True
                self.interrupt_measurement()

            if self.measurement_type=='hpc':
                excitation = self.excitation_hpc[:, 0]
            else:
                excitation = self.excitation[:, 0]

            sample_length = np.size(excitation, 0)
            start = self.playback_index
            end = start+frame_count

            if end >= sample_length:
                chunk = np.append(excitation[start:sample_length], np.zeros(end - sample_length))
                self.playback_index = 0
                self.playback_index = None

                self.playback_done.set()
            else:
                chunk = excitation[start:end]
                self.playback_index = end

            #print(f"Start: {start}, End: {end}, chunksize: {chunk.shape}, sample_length: {sample_length}, size_interleaved: {interleaved.size}")
            print(f"PLAY Start: {start}, End: {end}")

            # copy the excitation signal to the desired output channels
            for i in range(len(self.channel_layout_output)):
                if self.channel_layout_output[i] >= 0:
                    interleaved[self.channel_layout_output[i]::self.num_output_channels_used] = chunk

        return (interleaved.astype(np.float32).tostring(), pyaudio.paContinue)

    def audio_callback_input(self, in_data, frame_count, time_info, status):

        if self.recording_index is not None:

            if status != 0:
                self.measurement_error = True
                self.interrupt_measurement()

            buffer_length = np.size(self.recording_buffer, 0)
            start = self.recording_index
            end = start + frame_count

            input = np.fromstring(in_data, dtype=np.float32)

            if end >= buffer_length:
                end = buffer_length
                num_samples_to_copy = buffer_length - start
                self.recording_index = None
                print("LAST RECORD BUFFER")

            else:
                num_samples_to_copy = frame_count
                self.recording_index = end

            for i in range(self.num_input_channels_used):
                self.recording_buffer[start:end, i] = input[i:num_samples_to_copy*self.num_input_channels_used:self.num_input_channels_used]

            print(f"RECORD Start: {start}, End: {end}")

            # AFTER last buffer is written, notify that recording is done
            if self.recording_index is None:
                print("SENDING RECORDING DONE SIGNAL")
                self.recording_done.set()

        return (None, pyaudio.paContinue)

    def single_measurement(self, type=None):


        self.recorded_sweep_l = []
        self.recorded_sweep_r = []
        self.feedback_loop = []


        if not self.dummy_debugging:
            time.sleep(0.3)


        self.playback_index = 0
        self.recording_index = 0
        self.measurement_type = type

        if type=='hpc':
            self.recording_buffer = np.zeros((np.size(self.excitation_hpc, 0), self.num_input_channels_used))
        else:
            self.recording_buffer = np.zeros((np.size(self.excitation, 0), self.num_input_channels_used))

        print("Waiting for measuement...")
        self.playback_done.wait()
        self.playback_done.clear()

        print("Playback Done")

        self.recording_done.wait()
        self.recording_done.clear()
        print("Recording Done")

        self.recording_index = None
        self.playback_index = None

        # TODO handle measurement errors!
        if self.measurement_error:
            print("Measurement Failed due to audio error!")
        else:
            print("Measurement Succeeded")


        # get the recorded signals
        if self.channel_layout_input[0] >= 0:
            self.recorded_sweep_l = self.recording_buffer[:, self.channel_layout_input[0]]
        else:
            self.recorded_sweep_l = np.random.random_sample(np.size(self.recording_buffer, 0)) * 0.000001

        if self.channel_layout_input[1] >= 0:
            self.recorded_sweep_r = self.recording_buffer[:, self.channel_layout_input[1]]
        else:
            self.recorded_sweep_r = np.random.random_sample(np.size(self.recording_buffer, 0)) * 0.000001

        if self.feedback_loop_used:
            self.feedback_loop = self.recording_buffer[:, self.channel_layout_input[2]]
        else:
            # if no FB loop, copy from original excitation sweep
            if type is 'hpc':
                self.feedback_loop = self.sweep_hpc_mono[:, 0]
            else:
                self.feedback_loop = self.sweep_mono[:, 0]

        if abs(self.feedback_loop.max()) < 0.0001:
            self.feedback_loop = np.random.random_sample(self.feedback_loop.shape) * 0.000001  # to avoid zero-division errors

        self.recording_buffer = None



    def get_recordings(self):
        return [self.recorded_sweep_l, self.recorded_sweep_r, self.feedback_loop]

    def get_irs(self, rec_l=None, rec_r=None, fb_loop=None, deconv_fc_hp = None, deconv_fc_lp = None):
        try:
            if rec_l is None:
                rec_l = self.recorded_sweep_l
            if rec_r is None:
                rec_r = self.recorded_sweep_r
            if fb_loop is None:
                fb_loop = self.feedback_loop
            if deconv_fc_hp is None:
                deconv_fc_hp = self.sweep_parameters['f_start'] * 2
            if deconv_fc_lp is None:
                deconv_fc_lp = 20000

            ir_l = deconvolve(fb_loop, rec_l, self.audio_settings.samplerate, lowpass=[deconv_fc_lp, 4, 2], highpass=[deconv_fc_hp, 4, 2])
            ir_r = deconvolve(fb_loop, rec_r, self.audio_settings.samplerate, lowpass=[deconv_fc_lp, 4, 2], highpass=[deconv_fc_hp, 4, 2])
            return [ir_l, ir_r]
        except:
            return
