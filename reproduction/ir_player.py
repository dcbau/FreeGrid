import sounddevice as sd
import scipy.io
import scipy.io.wavfile as wave
import numpy as np


class IR_player():
    def __del__(self):
        print("DELETE")

    def __init__(self, IR_filepath='measured_points_david_02_09.mat', audiofile_path='Resources/evaluation_samples/epiano2.wav', interpolate_circular=False):
        print("INIT")

        self.interp_circ = interpolate_circular

        IR_filepath = 'measured_points_david_02_09.mat'
        self.irs = scipy.io.loadmat(IR_filepath)['dataIR']
        self.sourcePositions = scipy.io.loadmat(IR_filepath)['sourcePositions']

        if interpolate_circular:
            # filter out all BRIRs with elevation
            max_elevation = 10
            ids_horizontal = np.where(abs(self.sourcePositions[:, 1]) < max_elevation)
            ids_horizontal = np.array([0, 5, 15])
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


        try:
            fs, sample = scipy.io.wavfile.read(audiofile_path)
        except:
            print("File not loaded")
            return False

        # pre-convolve sample with every BRIR
        self.M = np.size(self.irs, axis=0)
        self.Nsample = np.size(sample, axis=0)
        self.samples_bin = scipy.signal.fftconvolve(self.irs, np.tile(sample[:, 0], (self.M, 2, 1)), axes=2)
        self.Nfull = np.size(self.samples_bin, axis=2)

        maxval = self.samples_bin.max()
        self.samples_bin = self.samples_bin / (maxval*2)

        # store source positions as cartesian vectors
        self.positions_xyz = self.sph2cart(self.sourcePositions[:, 0], self.sourcePositions[:, 1])

        print("Loaded " + str(self.M) + " BRIRs")

        self.current_BRIR_id = 0
        self.updated_BRIR_id = 0


        self.interpolation_ids = np.array((0, 1))
        self.interpolation_weights = np.array((0, 1))

        self.last_interpolation_ids = np.array((0, 1))
        self.last_interpolation_weights = np.array((0, 1))
        # other stuff
        self.theta = 0
        self.fs = fs
        self.stream = sd.OutputStream(samplerate=self.fs,
                                      channels=2,
                                      callback=self.audio_callback)



    def start(self):
        self.stream.start()

    def stop(self):
        self.stream.stop()

    def update_position(self, az, el):

        if self.interp_circ:
            # find next neighbors
            pos1 = np.where(self.sourcePositions[:, 0] <= az)[0][-1]
            pos2 = pos1 + 1


            # inverse distance weights
            d1 = np.abs(self.sourcePositions[pos1, 0] - az)
            d2 = np.abs(self.sourcePositions[pos2, 0] - az)
            w1 = d2 / (d1+d2)
            w2 = d1 / (d1+d2)

            self.interpolation_ids = np.array((pos1, pos2))
            self.interpolation_weights = np.array((w1, w2))
        else:
            currentPos = self.sph2cart(az, el)

            dist = np.zeros(self.M)


            for idx in range(self.M):
                dist[idx] = np.linalg.norm(currentPos - self.positions_xyz[:, idx])

            self.updated_BRIR_id = np.argmin(dist)

            #print(f'ID: {idx}  Real Angle: {az:.2f}  {el:.2f}')

            print(f'ID: {self.current_BRIR_id}  Angle: {self.sourcePositions[self.current_BRIR_id, 0]:.2f}  {self.sourcePositions[self.current_BRIR_id, 1]:.2f}')

    def sph2cart(self, _az, _el, ra=1):
        # convention: - el = -90...+90°,
        #            - x-axis = (0°|0°)
        #            - y-axis = (90°|0°)

        e = 90 - _el
        a = _az * np.pi / 180
        e = e * np.pi / 180

        x = ra * np.multiply(np.cos(a), np.sin(e))
        y = ra * np.multiply(np.sin(a), np.sin(e))
        z = ra * np.cos(e)

        position = np.array([x, y, z])

        return position

    def audio_callback(self, outdata, frames, time, status):

        i = (self.theta + np.arange(frames)) % self.Nsample

        # use a squared cosine fade for blending
        fade = np.power(np.cos(np.linspace(0, np.pi * 0.5, frames)), 2)

        print(f'ID1: {self.interpolation_ids[0]}   W1: {self.interpolation_weights[0]}')
        print(f'ID2: {self.interpolation_ids[1]}   W2: {self.interpolation_weights[1]}')

        if self.interp_circ:
            id1 = self.last_interpolation_ids[0]
            id2 = self.last_interpolation_ids[1]

            id1_new = self.interpolation_ids[0]
            id2_new = self.interpolation_ids[1]

            out_l_1 = self.samples_bin[id1, 0, i] * fade * self.last_interpolation_weights[0] \
                      + self.samples_bin[id1_new, 0, i] * (1 - fade) * self.interpolation_weights[0]
            out_r_1 = self.samples_bin[id1, 1, i] * fade * self.last_interpolation_weights[0] \
                      + self.samples_bin[id1_new, 1, i] * (1 - fade) * self.interpolation_weights[0]

            out_l_2 = self.samples_bin[id2, 0, i] * fade * self.last_interpolation_weights[1] \
                      + self.samples_bin[id2_new, 0, i] * (1 - fade) * self.interpolation_weights[1]
            out_r_2 = self.samples_bin[id2, 1, i] * fade * self.last_interpolation_weights[1] \
                      + self.samples_bin[id2_new, 1, i] * (1 - fade) * self.interpolation_weights[1]

            out_l = out_l_1 + out_l_2
            out_r = out_r_1 + out_r_2

            self.last_interpolation_ids = self.interpolation_ids
            self.last_interpolation_weights = self.interpolation_weights

        else:


            id = self.current_BRIR_id
            id_new = self.updated_BRIR_id
            self.current_BRIR_id = np.array(self.updated_BRIR_id)


            out_l = self.samples_bin[id, 0, i] * fade + self.samples_bin[id_new, 0, i] * (1-fade)
            out_r = self.samples_bin[id, 1, i] * fade + self.samples_bin[id_new, 1, i] * (1-fade)



        self.theta = (self.theta + frames) % self.Nsample

        outdata[:, 0] = out_l
        outdata[:, 1] = out_r
