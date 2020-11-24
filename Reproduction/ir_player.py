import sounddevice as sd
import scipy.io
import scipy.io.wavfile as wave
import numpy as np


class IR_player():
    def __del__(self):
        print("DELETE")

    def __init__(self, IR_filepath, audiofile_path='Resources/evaluation_samples/epiano2.wav'):
        print("INIT")

        self.irs = scipy.io.loadmat(IR_filepath)['dataIR']
        self.sourcePositions = scipy.io.loadmat(IR_filepath)['sourcePositions']

        try:
            fs, sample = scipy.io.wavfile.read(audiofile_path)
        except:
            print("File not loaded")
            return False

        # pre-convolve sample with every BRIR
        self.M = np.size(self.irs, axis=0)
        self.samples_bin = scipy.signal.fftconvolve(self.irs, np.tile(sample[:, 0], (self.M, 2, 1)), axes=2)
        self.N = np.size(self.samples_bin, axis=2)

        # store source positions as cartesian vectors
        self.positions_xyz = self.sph2cart(self.sourcePositions[:, 0], self.sourcePositions[:, 1])

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
        currentPos = self.sph2cart(az, el)

        dist = np.zeros(self.M)
        for idx, pos in enumerate(self.positions_xyz):
            dist[idx] = np.linalg.norm(currentPos - pos)

        self.current_BRIR_id = np.argmin(dist)

        print("ID: " + idx + "   Angle: " + self.sourcePositions[idx, 0] + self.sourcePositions[idx, 1])


    def sph2cart(self, _az, _el, ra=1):
        # convention: - el = -90...+90°,
        #            - x-axis = (0°|0°)
        #            - y-axis = (90°|0°)

        e = 90 - _el
        a = _az * np.pi / 180
        e = _el * np.pi / 180

        x = ra * np.multiply(np.cos(a), np.sin(e))
        y = ra * np.multiply(np.sin(a), np.sin(e))
        z = ra * np.cos(e)

        position = np.array([x, y, z])

        return position

    def audio_callback(self, outdata, frames, time, status):

        out_l = np.zeros(frames)
        out_r = np.zeros(frames)
        id = self.current_BRIR_id

        for sample in range(frames):

            out_l[sample] = self.samples_bin[id, 0, self.theta]
            out_r[sample] = self.samples_bin[id, 1, self.theta]

            self.theta += 1
            if self.theta >= self.N:
                self.theta = 0

        out_l = out_l.reshape(-1, 1)
        out_r = out_r.reshape(-1, 1)
        outdata[:, 0] = out_l
        outdata[:, 1] = out_r