import sounddevice as sd
import grid_improving.grid_filling
import numpy as np
from enum import Enum

class GuidingPhase(Enum):
    no_guiding = 0
    guiding_horizontal = 1
    guiding_vertical = 2

class PointRecommender():
    def __init__(self, tracker_ref):
        self.tracker = tracker_ref
        self.guiding_phase = GuidingPhase.no_guiding
        self.current_guiding_point = 0
        self.angular_accurancy = 5;
        self.target_view = []
        self.target_angle = []


    ## existing_pointset: Mx2 numpy array with angles az=0..360, el= -90..+90

    def start_guided_measurement(self, az_target, el_target):
        az_target = np.reshape(np.array([0, 60, 120, 180, 240, 300]), (6, 1))
        el_target = np.reshape(np.array([30, 0, -30]), (3, 1))

        az_target = np.tile(az_target, (3, 1))
        el_target = np.repeat(el_target, 6, axis=0)

        self.target_angle['az'] = az_target
        self.target_angle['el'] = el_target

        self.target_view['yaw'], self.target_view['pitch'], self.target_view['roll'] = self.get_head_rotation_to_point(az_target, el_target)
        self.guiding_phase = GuidingPhase.guiding_horizontal_angle
        self.playsound(event='guide_yaw', angle = self.target_view['yaw'])

    def update_position(self, current_az, current_el):

        if self.guiding_phase == GuidingPhase.guiding_horizontal:

            if abs(current_az - self.target_view['yaw']) < self.angular_accurancy:

                if self.target_view['pitch'] != 0:
                    self.playsound(event='guide_pitch', angle=self.target_view['pitch'])
                    self.guiding_phase = GuidingPhase.guiding_vertical
                elif self.target_view['roll'] != 0:
                    self.playsound(event='guide_roll', angle=self.target_view['roll'])
                    self.guiding_phase = GuidingPhase.guiding_vertical
                else:
                    self.playsound(event='point_reached')
                    self.guiding_phase = GuidingPhase.no_guiding
                    return True

        if self.guiding_phase == GuidingPhase.guiding_vertical:

            if abs(current_az - self.target_angle['az']) < self.angular_accurancy \
                    and abs(current_el - self.target_angle['el']) < self.angular_accurancy:
                self.playsound(event='point_reached')
                self.guiding_phase = GuidingPhase.no_guiding
                return True

        return False





    def playsound(self, event, angle=0):
        pass

    def recommend_new_points(self, existing_pointset, num_new_points):

        existing_pointset[:, 1] = 90 - existing_pointset[:, 1]
        newpoints = grid_improving.grid_filling.addSamplepoints(existing_pointset, 1)

        az = newpoints[:, 0]
        el = 90 - newpoints[:, 1]

        return az, el

    def get_head_rotation_to_point(self, az, el):
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
        [yaw1, pitch1] = self.vertical2interauralCoordinates(az, el)

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
        [yaw2, roll2] = self.vertical2frontalCoordinates(az, el)

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




    def vertical2interauralCoordinates(self, az, el):
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

    def vertical2frontalCoordinates(self, az, el):
        '''
        Converting from "vertical-polar" (first rotatation around the
        vertical axis -> poles are on the vertical axis) to "frontal-polar" (first
        rotatation is around the frontal axis & poles are on the frontal axis)

        The returned elevation corresponds to a lateral elevation (like a roll movement of the head)
        '''
        el = np.deg2rad(el)
        az = np.deg2rad(az)

        el_frontal = np.arctan(np.tan(el) / np.sin(az))
        az_frontal = np.arcsin(np.cos(el) * np.cos(az))

        az_frontal = np.rad2deg(az_frontal)
        el_frontal = np.rad2deg(el_frontal)

        return az_frontal, el_frontal