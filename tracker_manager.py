from ctypes import Array
from typing import Optional

from openvr import *
import time
import numpy as np
#import pyshtools
from pyquaternion import Quaternion


class Device():
    def __init__(self, type, id, is_available=False, is_active = False):
        self.type = type
        self.id = id
        self.isAvailable = is_available
        self.isActive = is_active

    def set_availability(self, is_available):
        self.isAvailable = is_available

    def is_available(self):
        return self.isAvailable

    def get_id(self):
        return self.id

class pose():
    def __init__(self, x_left, y_up, z_forward, translation):
        self.x_left = x_left
        self.y_up = y_up
        self.z_forward = z_forward
        self.translation = translation

def convert_to_quaternion(pose_mat):
    # Per issue #2, adding a abs() so that sqrt only results in real numbers
    r_w = np.sqrt(abs(1+pose_mat[0][0]+pose_mat[1][1]+pose_mat[2][2]))/2
    r_x = (pose_mat[2][1]-pose_mat[1][2])/(4*r_w)
    r_y = (pose_mat[0][2]-pose_mat[2][0])/(4*r_w)
    r_z = (pose_mat[1][0]-pose_mat[0][1])/(4*r_w)

    return np.array([r_w,r_x,r_y,r_z])

class TrackerManager():


        def __init__(self):

            self.fallback_angle = np.array([0.0, 0.0, 1.0])
            self.trackers_switched = False
            self.counter = 0

            self.offset_cm = {
                'speaker_z': 6,
                'speaker_y': 7,
                'head_y': 15
            }

            # initialize open VR
            try:
                self.vr_system = init(VRApplication_Background)
            except:
                print("Hell NO!")
                return

            # get available trackers and controllers


            for deviceID in range(k_unMaxTrackedDeviceCount):
                dev_class = self.vr_system.getTrackedDeviceClass(deviceID)
                if(dev_class == TrackedDeviceClass_GenericTracker):
                    if(not hasattr(self, 'tracker1')):
                        if self.vr_system.isTrackedDeviceConnected(deviceID):
                            self.tracker1 = Device(TrackedDeviceClass_GenericTracker, deviceID)
                            self.tracker1.set_availability(True)
                    elif (not hasattr(self, 'tracker2')):
                        if self.vr_system.isTrackedDeviceConnected(deviceID):
                            self.tracker2 = Device(TrackedDeviceClass_GenericTracker, deviceID)
                            self.tracker2.set_availability(True)
                elif(dev_class == TrackedDeviceClass_Controller):
                    if(not hasattr(self, 'controller1')):
                        self.controller1 = Device(TrackedDeviceClass_Controller, deviceID)
                        self.controller1.set_availability(self.vr_system.isTrackedDeviceConnected(deviceID))
                    elif (not hasattr(self, 'controller2')):
                        self.controller2 = Device(TrackedDeviceClass_Controller, deviceID)
                        self.controller2.set_availability(self.vr_system.isTrackedDeviceConnected(deviceID))


            if(hasattr(self, 'tracker1')):
                print("Has tracker one!")
                if(self.tracker1.is_available()):
                    print("Tracker 1 Available")

            if (hasattr(self, 'tracker2')):
                print("Has tracker two!")
                if (self.tracker2.is_available()):
                    print("Tracker 2 Available")

            if (hasattr(self, 'controller1')):
                print("Has controller 1!")

            if (hasattr(self, 'controller2')):
                print("Has controller 2!")


            self.calibrationRotation = Quaternion()
            self.calibrate_orientation()

            self.ear_pos_l = None
            self.ear_pos_r = None
            self.ear_center = None
            self.head_diameter = None

            self.acoustical_center_pos = None

            self.offset_mode = 'calibrated'




        def checkForTriggerEvent(self):

            #print("Check for Trigger Event")
            if (hasattr(self, 'controller1')):
                result, controllerState = self.vr_system.getControllerState(self.controller1.id)
                inputs = self.from_controller_state_to_dict(controllerState)
                if(bool(controllerState.ulButtonPressed >> 2 & 1)):
                    print("Button Pressed 1")
                    return True

            if (hasattr(self, 'controller2')):
                result, controllerState = self.vr_system.getControllerState(self.controller2.id)
                if (bool(controllerState.ulButtonPressed >> 2 & 1)):
                    print("Button Pressed 2")
                    return True

            return False

        def from_controller_state_to_dict(self, pControllerState):
            # docs: https://github.com/ValveSoftware/openvr/wiki/IVRSystem::GetControllerState
            d = {}
            d['unPacketNum'] = pControllerState.unPacketNum
            # on trigger .y is always 0.0 says the docs
            d['trigger'] = pControllerState.rAxis[1].x
            # 0.0 on trigger is fully released
            # -1.0 to 1.0 on joystick and trackpads
            d['trackpad_x'] = pControllerState.rAxis[0].x
            d['trackpad_y'] = pControllerState.rAxis[0].y
            # These are published and always 0.0
            # for i in range(2, 5):
            #     d['unknowns_' + str(i) + '_x'] = pControllerState.rAxis[i].x
            #     d['unknowns_' + str(i) + '_y'] = pControllerState.rAxis[i].y
            d['ulButtonPressed'] = pControllerState.ulButtonPressed
            d['ulButtonTouched'] = pControllerState.ulButtonTouched
            # To make easier to understand what is going on
            # Second bit marks menu button
            d['menu_button'] = bool(pControllerState.ulButtonPressed >> 1 & 1)
            # 32 bit marks trackpad
            d['trackpad_pressed'] = bool(pControllerState.ulButtonPressed >> 32 & 1)
            d['trackpad_touched'] = bool(pControllerState.ulButtonTouched >> 32 & 1)
            # third bit marks grip button
            d['grip_button'] = bool(pControllerState.ulButtonPressed >> 2 & 1)
            # System button can't be read, if you press it
            # the controllers stop reporting
            return d

        def trigger_haptic_impulse(self):
            return

            if (hasattr(self, 'controller1')):
                id = self.controller1.id
            else:
                id = self.controller2.id
            for i in range(1000):
                self.vr_system.triggerHapticPulse(id, 1, 1000)


        def calibrate_orientation(self):

            print("Calibration")

            try:
                pose_base, pose_relative = self.get_tracker_data()
            except:
                return

            head_tracker = Quaternion(convert_to_quaternion(pose_base))
            reference_tracker = Quaternion(convert_to_quaternion(pose_relative))

            self.calibrationRotation = head_tracker.inverse * reference_tracker


        # Valid modes:
        # - 'calibrated': use trackers to get the ear offset and acoustic center offset
        # - 'manual': set the offset by hand using the number boxes in the gui
        def set_offset_mode(self, mode):
            self.offset_mode = mode


        def calibrate_ear(self, ear):
            print("Calibrate Ear")

            try:
                pose_head, pose_ear = self.get_tracker_data()
            except:
                return False

            translation_head = np.array([pose_head.m[0][3], pose_head.m[1][3], pose_head.m[2][3]])
            translation_ear = np.array([pose_ear.m[0][3], pose_ear.m[1][3], pose_ear.m[2][3]])

            if ear == 'left':
                self.ear_pos_l = translation_head - translation_ear
            if ear == 'right':
                self.ear_pos_r = translation_head - translation_ear

            if self.ear_pos_l is not None and self.ear_pos_r is not None:
                # calculate center of head
                self.ear_center = (self.ear_pos_r + self.ear_pos_l) / 2
                self.head_diameter = np.linalg.norm(self.ear_pos_l - self.ear_pos_r)

            return True

        #this calibration assumes that the speaker is not moved after the calibration
        def calibrate_acoustical_center(self):
            print('Calibrate Acoustical Centre')
            try:
                pose_head, pose_acenter = self.get_tracker_data()
            except:
                return False

            self.acoustical_center_pos = np.array([pose_acenter.m[0][3], pose_acenter.m[1][3], pose_acenter.m[2][3]])

            return True



        def switch_trackers(self):
            if self.trackers_switched:
                self.trackers_switched = False
            else:
                self.trackers_switched = True

        def get_relative_position(self):

            try:
                pose_head, pose_speaker = self.get_tracker_data()

            except:
                return self.fallback_angle[0], self.fallback_angle[1], self.fallback_angle[2]

            if pose_head != False and pose_speaker != False:

                # MYSTERIOUS PROBLEM: The Y and Z Axis are flipped in the TrackerPose from openVR most of the times.
                mystery_flag = True #for testing debugging

                # STEP1: get the correct translation between head and speaker

                translation_head = np.array([pose_head.m[0][3], pose_head.m[1][3], pose_head.m[2][3]])
                translation_speaker = np.array([pose_speaker.m[0][3], pose_speaker.m[1][3], pose_speaker.m[2][3]])

                if self.offset_mode == 'calibrated' and self.ear_center is not None:
                    translation_head = translation_head + self.ear_center
                else:
                    # offset from ears to tracker
                    # true head center lies below the tracker (negative y direction), so we translate the pose matrix "down"
                    if mystery_flag:
                        offset_y_vector = self.offset_cm['head_y'] * 0.01 * np.array([pose_head.m[0][2], pose_head.m[1][2], pose_head.m[2][2]])
                    else:
                        offset_y_vector = -self.offset_cm['head_y'] * 0.01 * np.array([pose_head.m[0][1], pose_head.m[1][1], pose_head.m[2][1]])

                    translation_head = translation_head + offset_y_vector

                if self.offset_mode == 'calibrated' and self.acoustical_center_pos is not None:
                    translation_speaker = self.acoustical_center_pos
                else:
                    # offset from speaker center to tracker
                    if mystery_flag:
                        offset_y_vector = self.offset_cm['speaker_y'] * 0.01 * np.array([pose_speaker.m[0][2], pose_speaker.m[1][2], pose_speaker.m[2][2]])
                        offset_z_vector = self.offset_cm['speaker_z'] * 0.01 * np.array([pose_speaker.m[0][1], pose_speaker.m[1][1], pose_speaker.m[2][1]])
                    else:
                        offset_y_vector = -self.offset_cm['speaker_y'] * 0.01 * np.array([pose_speaker.m[0][1], pose_speaker.m[1][1], pose_speaker.m[2][1]])
                        offset_z_vector = self.offset_cm['speaker_z'] * 0.01 * np.array([pose_speaker.m[0][2], pose_speaker.m[1][2], pose_speaker.m[2][2]])
                    translation_speaker = translation_speaker + offset_y_vector + offset_z_vector


                # get vector pointing from head center to speaker center
                transvec = translation_speaker - translation_head

                # STEP2: get the correct orientation of the head

                # get the base tracker rotation in quaternions
                fwd = np.array([pose_head.m[0][2], pose_head.m[1][2], pose_head.m[2][2]])
                up = np.array([pose_head.m[0][1], pose_head.m[1][1], pose_head.m[2][1]])
                side = np.array([pose_head.m[0][0], pose_head.m[1][0], pose_head.m[2][0]])

                r_w = np.sqrt(abs(1 + side[0] + up[1] + fwd[2])) / 2
                r_x = (up[2] - fwd[1]) / (4 * r_w)
                r_y = (fwd[0] - side[2]) / (4 * r_w)
                r_z = (side[1] - up[0]) / (4 * r_w)

                head_rotation = Quaternion(r_w, r_x, r_y, r_z)

                # apply calibrated rotation
                rotation = head_rotation * self.calibrationRotation

                # make "new' direction vectors by rotating a normed set of orthogonal direction vectors

                if mystery_flag:
                    side = np.array([1.0, 0.0, 0.0])
                    up = np.array([0.0, 0.0, -1.0]) # i don´t know why, but y and z axis are flipped somehow
                    fwd = np.array([0.0, 1.0, 0.0]) #
                else:
                    side = np.array([1.0, 0.0, 0.0])
                    up = np.array([0.0, 1.0, 0.0])
                    fwd = np.array([0.0, 0.0, 1.0])

                side = rotation.rotate(side)
                up = rotation.rotate(up)
                fwd = rotation.rotate(fwd)

                # STEP3: calculate direction vector to speaker relative to head coordinate system
                # (head coordinate system = side, up, fwd)

                direction_vector = np.array([np.inner(side, transvec), np.inner(up, transvec), np.inner(fwd, transvec)])
                radius = np.linalg.norm(direction_vector)
                direction_vector = direction_vector / radius

                # get spherical coordinates from direction vector
                az = np.rad2deg(np.arctan2(-direction_vector[0], -direction_vector[2]))
                if az < 0:
                    az += 360

                el = np.rad2deg(np.arccos(-direction_vector[1]))
                el = el - 90


                #print(az, el, radius)
                return az, el, radius

        def get_tracker_data(self):

            #poseMatrix1 = []
            #poseMatrix2 = []

            pose = self.vr_system.getDeviceToAbsoluteTrackingPose(TrackingUniverseStanding,
                                                                  0,
                                                                  k_unMaxTrackedDeviceCount)
            pose1 = pose[self.tracker1.id]
            if pose1.bDeviceIsConnected:
                self.tracker1.isAvailable = True
                if pose1.bPoseIsValid:
                        self.tracker1.isActive = True
                        poseMatrix1 = pose1.mDeviceToAbsoluteTracking
                else:
                        self.tracker1.isActive = False
            else:
                self.tracker1.isAvailable = False

            pose2 = pose[self.tracker2.id]
            if pose2.bDeviceIsConnected:
                self.tracker2.isAvailable = True
                if pose2.bPoseIsValid:
                    self.tracker2.isActive = True
                    poseMatrix2 = pose2.mDeviceToAbsoluteTracking
                else:
                    self.tracker1.isActive = False
            else:
                self.tracker1.isAvailable = False

            if self.trackers_switched:
                return poseMatrix2, poseMatrix1
            else:
                 return poseMatrix1, poseMatrix2


        def set_angle_manually(self, azimuth, elevation):
            self.fallback_angle[0] = float(azimuth)
            self.fallback_angle[1] = float(elevation)


        def check_tracker_availability(self):
            tracker_status = {
                "tracker1": "Unavailable",
                "tracker2": "Unavailable"
            }
            if (hasattr(self, 'tracker1')):
                if self.tracker1.isActive:
                    tracker_status['tracker1'] = "Tracking"
                elif self.tracker1.isAvailable:
                    tracker_status['tracker1'] = "Available / Not tracking"

            if (hasattr(self, 'tracker2')):
                if self.tracker2.isActive:
                    tracker_status['tracker2'] = "Tracking"
                elif self.tracker2.isAvailable:
                    tracker_status['tracker2'] = "Available / Not tracking"

            return tracker_status




