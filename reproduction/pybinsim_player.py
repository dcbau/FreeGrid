from reproduction import pybinsim
import threading
import numpy as np
import scipy.io
import wave
from pythonosc import udp_client
#import os
import os
import shutil

class PyBinSim_Player():
    def __init__(self, IR_filepath='Measurements/measured_points_david_02_09.mat', audiofile_path='Resources/evaluation_samples/epiano2.wav', interpolate_circular=False):

        #IR_filepath= 'Measurements/measured_points_david_brirs_11_12_2020.mat'
        self.loadDataset(IR_filepath)


        self.oscIdentifier = '/pyBinSim'
        ip = '127.0.0.1'
        port = 10000
        nSources = 1
        self.minAngleDifference=1
        self.previous_az = 0

        self.client = udp_client.SimpleUDPClient(ip, 10000)

        self.binsim = pybinsim.BinSim('reproduction/pybinsim_resources/config/config.cfg')

    def close(self):
        self.binsim.__exit__(None, None, None)

    def update_position(self, az, el):
        az_int = int(np.floor(az))
        if self.previous_az != az_int:
            binSimParapmeters = [0, az_int, 0, 0, 0, 0, 0]
            print('Select Az: ', az_int)
            self.client.send_message(self.oscIdentifier, binSimParapmeters)

    def start(self):
        self.binsim.stream_start()

    def register_instance(self, pybinsim_instance):
        self.pbs_instance = pybinsim_instance

    def stop(self):
        self.binsim.stream_close()

    def loadDataset(self, path, only_circ=True, max_elevation=5, blocksize=512, request_filter_length=24000):

        self.irs = scipy.io.loadmat(path)['dataIR']
        self.sourcePositions = scipy.io.loadmat(path)['sourcePositions']
        self.fs = scipy.io.loadmat(path)['fs']

        if only_circ:
            # filter out all BRIRs with elevation
            ids_horizontal = np.where(abs(self.sourcePositions[:, 1]) < max_elevation)
            ids_horizontal = np.squeeze(ids_horizontal)
            self.irs = self.irs[ids_horizontal, :, :]
            self.sourcePositions = self.sourcePositions[ids_horizontal, :]

            # sort ascending azimuth
            sort_idx = np.argsort(self.sourcePositions[:, 0])
            self.sourcePositions = self.sourcePositions[sort_idx, :]
            self.irs = self.irs[sort_idx, :, :]

            # add first measurement to end of grid and last measurement to start of grid
            # to ease interpolation at wrap around positions
            first_pos = np.array(self.sourcePositions[0, :]).reshape((1, 3))
            first_pos[0, 0] += 360
            last_pos = np.array(self.sourcePositions[-1, :]).reshape((1, 3))
            last_pos[0, 0] -= 360
            self.sourcePositions = np.concatenate((last_pos, self.sourcePositions, first_pos), axis=0)

            first_measurement = self.irs[0, :, :]
            first_measurement = np.expand_dims(first_measurement, axis=0)
            last_measurement = self.irs[-1, :, :]
            last_measurement = np.expand_dims(last_measurement, axis=0)

            self.irs = np.concatenate((last_measurement, self.irs, first_measurement), axis=0)


            # WINDOW & ALIGN
            filter_length = int(np.floor(request_filter_length/blocksize) * blocksize)
            fade_in_time = 100
            fade_out_time = 300

            onsets = self.detect_onset(self.irs)
            onsets = np.min(onsets, axis=1)

            M = np.size(self.irs, 0)
            C = np.size(self.irs, 1)

            irs_windowed = np.zeros([M, C, filter_length])

            fade_in = 1 - np.power(np.cos(np.linspace(0, np.pi * 0.5, fade_in_time)), 2)
            fade_out = np.power(np.cos(np.linspace(0, np.pi * 0.5, fade_out_time)), 2)

            win = np.ones(filter_length)
            win[:fade_in_time] = fade_in
            win[-fade_out_time:] = fade_out

            for m in range(M):
                for c in range(C):
                    start = onsets[m] - fade_in_time
                    end = start + filter_length
                    irs_windowed[m, c, :] = self.irs[m, c, start:end] * win



            export = {'irs_windowed': irs_windowed}

            scipy.io.savemat('Measurements/measured_points_david_02_09_windowed.mat', export)


            # upsampling!
            upsampling = True
            if upsampling:
                oversampling = 4
                NFFT = filter_length*oversampling
                complex_length = int(NFFT / 2 + 1)

                HRTF = np.fft.rfft(irs_windowed, n=NFFT, axis=2)

                mag = np.abs(HRTF)
                phase = np.unwrap(np.angle(HRTF))

                az_vals = np.arange(360)
                el_vals = np.zeros(360).astype(int)

                n_dense = np.size(az_vals)

                HRTF_interp = np.zeros([n_dense, C, complex_length])


                interpolation_ids = np.zeros(n_dense)
                for m in range(n_dense):
                    az = az_vals[m]

                    pos1 = np.where(self.sourcePositions[:, 0] <= az)[0][-1]
                    pos2 = pos1 + 1

                    d1 = np.abs(self.sourcePositions[pos1, 0] - az)
                    d2 = np.abs(self.sourcePositions[pos2, 0] - az)
                    w1 = d2 / (d1 + d2)
                    w2 = d1 / (d1 + d2)

                    interp_mag = mag[pos1, :, :] * w1 + mag[pos2, :, :] * w2
                    if d1 < d2:
                        interp_phase = phase[pos1, :, :]
                    else:
                        interp_phase = phase[pos2, :, :]

                    HRTF_interp[m, :, :] = interp_mag * np.exp(1j*interp_phase)

                dense_irs = np.fft.irfft(HRTF_interp, NFFT)[:, :, :filter_length]
                M = n_dense

            # make a pybinsim export set
            if not upsampling:
                az_vals = np.round(self.sourcePositions[:, 0]).astype(int)
                el_vals = np.zeros(np.size(az_vals)).astype(int)
                dense_irs = irs_windowed

            ir_export_path = 'reproduction/pybinsim_resources/BRIRs_CIRC360_pbs'
            ir_folder = os.path.join(ir_export_path, 'IRs')

            if not os.path.isdir(ir_export_path):
                os.mkdir(ir_export_path)
            if not os.path.isdir(ir_folder):
                os.mkdir(ir_folder)

            for file in os.listdir(ir_folder):
                filepath = os.path.join(ir_folder, file)
                try:
                    os.unlink(filepath)
                except Exception as e:
                    print('Failed to delete %s. %s\n' % (filepath, e))

            filterlist = open(os.path.join(ir_export_path, 'filterlist.txt'), 'w')

            for m in range(M):
                filename = f'ir_{az_vals[m]}_{el_vals[m]}.wav'
                filename_full = os.path.join(ir_folder, filename)

                ir = np.transpose(dense_irs[m, :, :])
                #ir = np.flip(ir, axis=1) # flip L R channels... somehow scipy wants the channels in reverse order???

                scipy.io.wavfile.write(filename_full, 48000, ir)

                filterlist.write(f'{az_vals[m]} {el_vals[m]} 0 0 0 0 {filename_full}\n')

            # add headphone compesation filter
            hpcf_path = 'reproduction/pybinsim_resources/hpirs/HPCF_David_HD660.wav'
            filterlist.write(f'HPFILTER {hpcf_path}\n')
            filterlist.close()

            # make the config file
            config_file_path = 'reproduction/pybinsim_resources/config/config.cfg'
            if os.path.isfile(config_file_path):
                os.unlink(config_file_path)

            configfile = open(config_file_path, 'w')
            configfile.write(f'soundfile reproduction/pybinsim_resources/signal/test_48k.wav\n')
            configfile.write(f'blockSize {blocksize}\n')
            configfile.write(f'filterSize {filter_length}\n')
            configfile.write(f'filterList reproduction/pybinsim_resources/BRIRs_CIRC360_pbs/filterlist.txt\n')
            configfile.write(f'maxChannels 2\n')
            configfile.write(f'samplingRate 48000\n')
            configfile.write(f'enableCrossfading False\n')
            configfile.write(f'useHeadphoneFilter False\n')
            configfile.write(f'loudnessFactor 1\n')

    def detect_onset(self, irs, onset_threshold_db=-6):
        #irs : [M C N] measurements x channels x samples

        M = np.size(irs, 0)
        C = np.size(irs, 1)

        maxvals = np.max(abs(irs), axis=2)
        onset_threshold = 10**(onset_threshold_db/20)
        onsets = np.zeros([M, C]).astype(int)

        for m in range(M):
            for c in range(C):
                onsets[m, c] = int(np.argmax(abs(irs[m, c, :]) >= maxvals[m, c]*onset_threshold))

        return onsets


