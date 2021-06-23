import sounddevice as sd
import grid_improving.grid_filling
import numpy as np
from enum import Enum
import scipy.io.wavfile as wave
import warnings

class GuidingPhase(Enum):
    no_guiding = 0
    guiding_horizontal = 1
    guiding_vertical = 2

class VoiceInstruction():
    def __init__(self):

        self.angles = {}
        for i in range(18):
            angle = (i+1)*10
            filename = str(angle) + "deg.wav"
            self.angles[angle] = self.loadfile(filename)

        self.turn_left = self.loadfile("turn_left.wav")
        self.turn_right = self.loadfile("turn_right.wav")
        self.tilt_left = self.loadfile("tilt_left.wav")
        self.tilt_right = self.loadfile("tilt_right.wav")
        self.tilt_down = self.loadfile("tilt_down.wav")
        self.tilt_up = self.loadfile("tilt_up.wav")

        self.intermediate_point_reached = self.loadfile("ok.wav")
        self.final_point_reached = self.loadfile("well_done.wav")

        self.fs = 48000



    def loadfile(self, filename, normalize=True):
        directory = 'Resources/voice_samples/'

        # suppress specific warning because reading the file "turn_right.wav" always triggered a warning
        warnings.simplefilter(action='ignore', category=wave.WavFileWarning)

        try:
            fs, file = wave.read(directory + filename)
        except FileNotFoundError:
            print("Resource file missing: " + filename)
            return []

        if fs != 48000:
            print("Samplerate of " + " is not supported. Only 48kH")
            return []

        if normalize:
            file = file * 0.5 / 32768 #devide by integer sample type and attenuate by -6dB
        return file

    def play_angle_instruction(self, rotation, angle):

        raster = 10
        rasterized_angle = int(abs(angle) - np.mod(abs(angle), raster/2) + raster/2)
        rasterized_angle = rasterized_angle - np.mod(rasterized_angle, raster)

        if rasterized_angle == 0:
            return
        if rotation == 'yaw':
            if angle >= 0:
                sound = np.append(self.turn_left, self.angles[rasterized_angle])
            else:
                sound = np.append(self.turn_right, self.angles[rasterized_angle])

        elif rotation == 'pitch':
            if angle >= 0:
                sound = np.append(self.tilt_up, self.angles[rasterized_angle])
            else:
                sound = np.append(self.tilt_down, self.angles[rasterized_angle])

        elif rotation == 'roll':
            if angle >= 0:
                sound = np.append(self.tilt_right, self.angles[rasterized_angle])
            else:
                sound = np.append(self.tilt_left, self.angles[rasterized_angle])

        sd.play(sound, self.fs)
        sd.wait()

    def play_event(self, event):

        if event == 'intermediate_point_reached':
            sd.play(self.intermediate_point_reached, self.fs)
        elif event == 'final_point_reached':
            sd.play(self.final_point_reached, self.fs)

        sd.wait()

class GuidingTone():
    def __init__(self, angular_accuracy=1, fs=48000):

        self.distance = angular_accuracy
        self.angular_accuracy = angular_accuracy

        # characteristics
        frequency = 300  # Hz
        amplitude = 0.1 # mag
        pulse_duration = 10  # cycles
        fade_length = 400  # samples
        self.gap_multi = 10  # angular distance -> gapwidt in ms * gap_multi (1° -> 1ms * gap_multi)

        # other stuff
        self.start_idx = 0
        self.fs = fs
        self.pulse = np.array([])
        self.stream = sd.OutputStream(samplerate=self.fs,
                                      channels=1,
                                      callback=self.audio_callback)

        # precalculate sinepulse
        T_sine = int(fs / frequency)
        t = np.arange(T_sine * pulse_duration)
        self.sine = amplitude * np.sin(2 * np.pi * t / T_sine)
        fade = np.arange(fade_length) / fade_length
        self.sine [:fade_length] = self.sine [:fade_length] * fade
        self.sine [-fade_length:] = self.sine [-fade_length:] * np.flip(fade)


    def start(self):
        self.stream.start()

    def stop(self):
        self.stream.stop()

    def update_distance(self, distance):
        self.distance = distance

    def audio_callback(self, outdata, frames, time, status):

        out = np.zeros(frames)
        for sample in range(frames):

            if self.start_idx <= 0:

                # at the beginning of every pulse, make the whole pulse cycle
                dist = self.distance - self.angular_accuracy
                if dist < 0:
                    dist = 0
                pulse_gap = dist * self.gap_multi * self.fs / 1000
                gap = np.zeros(int(pulse_gap))
                self.pulse = np.append(self.sine, gap)

                self.start_idx = np.size(self.pulse)

            # read out the pulse wave
            out[sample] = self.pulse[-self.start_idx]

            self.start_idx -= 1

        out = out.reshape(-1, 1)
        outdata[:] = out

class PointRecommender():
    def __init__(self, tracker_ref):
        self.tracker = tracker_ref
        self.guiding_phase = GuidingPhase.no_guiding
        self.current_guiding_point = 0
        self.angular_accuracy = 5
        self.target_view ={}
        self.target_angle = {}

        self.distance = 0

        self.voice_instructions = VoiceInstruction()

        self.guiding_tone = GuidingTone(self.distance)

    def start_guided_measurement(self, az_target, el_target):
        # az_target = np.reshape(np.array([0, 60, 120, 180, 240, 300]), (6, 1))
        # el_target = np.reshape(np.array([30, 0, -30]), (3, 1))
        #
        # az_target = np.tile(az_target, (3, 1))
        # el_target = np.repeat(el_target, 6, axis=0)

        az_target = az_target % 360
        self.target_angle['az'] = az_target % 360
        self.target_angle['el'] = el_target

        self.target_view['yaw'], self.target_view['pitch'], self.target_view['roll'] = get_head_rotation_to_point(az_target, el_target)
        if abs(self.target_view['yaw']) > self.angular_accuracy:
            self.guiding_phase = GuidingPhase.guiding_horizontal
            self.voice_instructions.play_angle_instruction(rotation='yaw', angle=self.target_view['yaw'])
            self.guiding_tone.start()
        else:
            self.guiding_phase = GuidingPhase.guiding_vertical
            if abs(self.target_view['pitch']) > self.angular_accuracy:
                self.voice_instructions.play_angle_instruction(rotation='pitch', angle=self.target_view['pitch'])
                self.guiding_phase = GuidingPhase.guiding_vertical
                self.guiding_tone.start()
            elif abs(self.target_view['roll']) > self.angular_accuracy:
                self.voice_instructions.play_angle_instruction(rotation='roll', angle=self.target_view['roll'])
                self.guiding_phase = GuidingPhase.guiding_vertical
                self.guiding_tone.start()
            else:
                self.guiding_phase = GuidingPhase.guiding_vertical

    def stop(self):
        self.guiding_tone.stop()
        self.guiding_phase = GuidingPhase.no_guiding

    def update_position(self, current_az, current_el):

        current_yaw_view = current_az if current_az < 180 else current_az - 360

        if self.guiding_phase == GuidingPhase.guiding_horizontal:

            self.distance = abs(current_yaw_view + self.target_view['yaw'])
            self.guiding_tone.update_distance(self.distance)

            if self.distance < self.angular_accuracy:
                self.guiding_tone.stop()

                if abs(self.target_view['pitch']) > self.angular_accuracy:
                    self.voice_instructions.play_event(event='intermediate_point_reached')
                    self.voice_instructions.play_angle_instruction(rotation='pitch', angle=self.target_view['pitch'])
                    self.guiding_phase = GuidingPhase.guiding_vertical
                    self.guiding_tone.start()
                elif abs(self.target_view['roll']) > self.angular_accuracy:
                    self.voice_instructions.play_event(event='intermediate_point_reached')
                    self.voice_instructions.play_angle_instruction(rotation='roll', angle=self.target_view['roll'])
                    self.guiding_phase = GuidingPhase.guiding_vertical
                    self.guiding_tone.start()
                else:
                    self.stop()
                    self.voice_instructions.play_event(event='final_point_reached')

                    return True

        if self.guiding_phase == GuidingPhase.guiding_vertical:

            self.distance = grid_improving.angular_distance.angularDistance(current_az,
                                                                   current_el,
                                                                   self.target_angle['az'],
                                                                   self.target_angle['el'])

            self.guiding_tone.update_distance(self.distance)
            if self.distance < self.angular_accuracy:
                self.stop()
                self.voice_instructions.play_event(event='final_point_reached')
                return True

        return False

    def recommend_new_points(self, _existing_pointset, num_new_points=1):

        existing_pointset = np.array(_existing_pointset, copy=True)

        existing_pointset[:, 1] = 90 - existing_pointset[:, 1]
        #newpoints = grid_improving.grid_filling.addSamplepoints(existing_pointset, 1)
        newpoints2 = grid_improving.grid_filling.addSamplepoints_geometric(existing_pointset, num_new_points)

        #print("NewPoints1: ")
        #print(newpoints)
        #print("NewPoints2: ")
        #print(newpoints2)

        az = newpoints2[:, 0] % 360
        el = 90 - newpoints2[:, 1]

        return az, el

def get_head_rotation_to_point(az, el):
    '''
    Gives the view direction (how to turn the head in a yaw and pitch/roll movement),
    so a speaker placed in frontal direction has the given azimuth and elevation
    relative to the head. To reduce backpain, the elevation is achived by either pitch OR roll,
    the unused return value is set to zero.
    @param az: Azimuth angle 0° ... 360°
    @param el: Elevation angle -90° ... - + 90°
    @return yaw, pitch, roll: View direction, either [yaw, pitch, 0] or [yaw, 0, roll]
    '''
    ## First angle version (yaw/pitch)

    # calculate angle
    [yaw1, pitch1] = vertical2interauralCoordinates(az, el)

    # modify yaw angles for directions behind the lateral plane (modification determined empirically)
    yaw1 = np.where((az > 90) & (az <= 270), 180 - yaw1,  yaw1)

    # restrict range
    yaw1 = np.where(yaw1 > 180, yaw1 - 360, yaw1)
    yaw1 = np.where(yaw1 < -180, yaw1 + 360, yaw1)

    # invert to make it a view direction
    yaw1 *= -1
    pitch1 *= -1

    ## Second angle version (yaw/roll)

    # calculate angle
    [yaw2, roll2] = vertical2frontalCoordinates(az, el)

    # modify yaw angles left/right side seperately (values determined empirically)
    yaw2 = np.where(az <= 180, 90 - yaw2, yaw2 - 90)

    # invert to make it a view direction
    yaw2 *= -1
    roll2 *= -1

    ## make new final list containing both movement options

    # select version where the elevation movement is smaller (easier to reach)
    yaw = np.where(np.abs(pitch1) > np.abs(roll2), yaw2, yaw1)
    pitch = np.where(np.abs(pitch1) > np.abs(roll2), 0, pitch1)
    roll = np.where(np.abs(pitch1) > np.abs(roll2), roll2, 0)

    return yaw, pitch, roll




def vertical2interauralCoordinates(az, el):
    '''
    Converting from "vertical-polar" (first rotatation around the
    vertical axis -> poles are on the vertical axis) to "interaural-polar" (first
    rotatation is around the interaural axis & poles are on the interaural axis)
    '''

    #Source:
    #Mattes et al, 2012: "Towards a human perceputal model for 3D sound localization"

    el = np.deg2rad(el)
    az = np.deg2rad(az)

    el_interaural = np.arctan(np.tan(el) / np.cos(az))
    az_interaural = np.arcsin(np.cos(el) * np.sin(az))

    az_interaural = np.rad2deg(az_interaural)
    el_interaural = np.rad2deg(el_interaural)

    return az_interaural, el_interaural

def vertical2frontalCoordinates(az, el):
    '''
    Converting from "vertical-polar" (first rotatation around the
    vertical axis -> poles are on the vertical axis) to "frontal-polar" (first
    rotatation is around the frontal axis & poles are on the frontal axis)

    The returned elevation corresponds to a lateral elevation (like a roll movement of the head)
    '''
    el = np.deg2rad(el)
    az = np.deg2rad(az)

    if az > np.pi:
        el_frontal = -np.arctan2(np.tan(el), -np.sin(az)) # little hack to comply to acot(cot(el) * sin(az))
    else:
        el_frontal = np.arctan2(np.tan(el), np.sin(az))

    az_frontal = np.arcsin(np.cos(el) * np.cos(az))

    az_frontal = np.rad2deg(az_frontal)
    el_frontal = np.rad2deg(el_frontal)

    return az_frontal, el_frontal