from openvr import *
import time
import numpy as np
#import pyshtools
from pyquaternion import Quaternion
from tracking import osc_input

import matplotlib
import matplotlib.pyplot as plt

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

            self.head_dimensions = {
                'ear_pos_l': None,
                'ear_pos_r': None,
                'ear_center': None,
                'left_pos': None,
                'right_pos': None,
                'head_width': None,
                'front_pos': None,
                'back_pos': None,
                'head_length': None
            }

            self.tracking_mode = "Vive"

            self.osc_input_server = None



            self.acoustical_center_pos = None


            self.vr_system_initialized = False

            # initialize open VR
            try:
                self.vr_system = init(VRApplication_Background)
            except:
                return

            self.vr_system_initialized = True
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


            # if(hasattr(self, 'tracker1')):
            #     #print("Has tracker one!")
            #     if(self.tracker1.is_available()):
            #         pass
            #         #print("Tracker 1 Available")
            #
            # if (hasattr(self, 'tracker2')):
            #     #print("Has tracker two!")
            #     if (self.tracker2.is_available()):
            #         pass
            #         #print("Tracker 2 Available")
            #
            # if (hasattr(self, 'controller1')):
            #     #print("Has controller 1!")
            #     pass
            #
            # if (hasattr(self, 'controller2')):
            #     #print("Has controller 2!")
            #     pass


            self.calibrationRotation = Quaternion()
            self.calibrate_orientation()


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

        def calibrate_orientation(self):

            #print("Calibration")

            try:
                pose_base, pose_relative = self.get_tracker_data()
            except:
                return False

            head_tracker = Quaternion(convert_to_quaternion(pose_base))
            reference_tracker = Quaternion(convert_to_quaternion(pose_relative))

            self.calibrationRotation = head_tracker.inverse * reference_tracker

            return True

        def calibrate_headdimensions(self, pos, multiple_calls=True):

            if multiple_calls:
                num_calls = 40
                time_window_s = 1
                inital_sleep = 2
                sleep_interval = time_window_s / num_calls

                pose_head_list = np.zeros([3, 4, num_calls])
                pose_ear_list = np.zeros([3, 4, num_calls])

                direction_vector_list = np.zeros([3, num_calls])
                valid_ids = np.full(num_calls, True, dtype=bool)

                time.sleep(inital_sleep) #inital sleep to calm down trackers

                for i in range(num_calls):
                    try:
                        pose_head_temp, pose_ear_temp = self.get_tracker_data()
                        pose_head = pose_head_temp.m
                        pose_ear = pose_ear_temp.m

                        translation_head = np.array([pose_head[0][3], pose_head[1][3], pose_head[2][3]])
                        translation_ear = np.array([pose_ear[0][3], pose_ear[1][3], pose_ear[2][3]])

                        transvec = translation_ear - translation_head

                        fwd = np.array([pose_head[0][2], pose_head[1][2], pose_head[2][2]])
                        up = np.array([pose_head[0][1], pose_head[1][1], pose_head[2][1]])
                        side = np.array([pose_head[0][0], pose_head[1][0], pose_head[2][0]])

                        direction_vector_list[:, i] = np.array([np.inner(transvec, side), np.inner(transvec, up), np.inner(transvec, fwd)])

                    except:
                        valid_ids[i] = False

                    time.sleep(sleep_interval)

                if valid_ids.max() == False:
                    return False

                #t = range(np.size(direction_vector_list, 1))
                #fig, ax = plt.subplots()
                #ax.plot(t, direction_vector_list[0, :])
                #ax.plot(t, direction_vector_list[1, :])
                #ax.plot(t, direction_vector_list[2, :])

                #ax.grid()

                #plt.show()

                try:
                    direction_vector = np.mean(direction_vector_list[:, valid_ids], axis=1)
                except:
                    return False

            else:
                try:
                    pose_head_temp, pose_ear_temp = self.get_tracker_data()
                    pose_head = pose_head_temp.m
                    pose_ear = pose_ear_temp.m
                except:
                    return False

                translation_head = np.array([pose_head[0][3], pose_head[1][3], pose_head[2][3]])
                translation_ear = np.array([pose_ear[0][3], pose_ear[1][3], pose_ear[2][3]])

                transvec = translation_ear - translation_head

                fwd = np.array([pose_head[0][2], pose_head[1][2], pose_head[2][2]])
                up = np.array([pose_head[0][1], pose_head[1][1], pose_head[2][1]])
                side = np.array([pose_head[0][0], pose_head[1][0], pose_head[2][0]])

                direction_vector = np.array([np.inner(transvec, side), np.inner(transvec, up), np.inner(transvec, fwd)])

            if pos == 'left_ear':
                self.head_dimensions['ear_pos_l'] = direction_vector
            if pos == 'right_ear':
                self.head_dimensions['ear_pos_r'] = direction_vector

            if pos == 'left':
                self.head_dimensions['left_pos'] = direction_vector
            if pos == 'right':
                self.head_dimensions['right_pos'] = direction_vector
            if pos == 'front':
                self.head_dimensions['front_pos'] = direction_vector
            if pos == 'back':
                self.head_dimensions['back_pos'] = direction_vector

            if self.head_dimensions['ear_pos_l'] is not None and self.head_dimensions['ear_pos_r'] is not None:
                self.head_dimensions['ear_center'] = (self.head_dimensions['ear_pos_r'] + self.head_dimensions['ear_pos_l']) / 2

            if self.head_dimensions['left_pos'] is not None and self.head_dimensions['right_pos'] is not None:
                self.head_dimensions['head_width'] = np.linalg.norm(self.head_dimensions['left_pos'] - self.head_dimensions['right_pos'])

            if self.head_dimensions['front_pos'] is not None and self.head_dimensions['back_pos'] is not None:
                self.head_dimensions['head_length'] = np.linalg.norm(self.head_dimensions['front_pos'] - self.head_dimensions['back_pos'])


            return True

        #this calibration assumes that the speaker is not moved after the calibration
        def calibrate_acoustical_center(self):
            #print('Calibrate Acoustical Centre')
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

            if self.tracking_mode == "OSC_direct":
                if self.osc_input_server is None:
                    self.osc_input_server = osc_input.OSCInputServer()
                    self.osc_input_server.start_listening()
                try:
                    angles = self.osc_input_server.get_current_angle()
                except:
                    return self.fallback_angle[0], self.fallback_angle[1], self.fallback_angle[2]

                return angles[0], angles[1], angles[2]

            try:
                if self.acoustical_center_pos is not None:
                    pose_head, _ = self.get_tracker_data(only_tracker_1=True)
                    translation_speaker = self.acoustical_center_pos
                else:
                    # if speaker is not calibrated yet, the live tracking speaker pose is used
                    pose_head, pose_speaker = self.get_tracker_data()
                    translation_speaker = np.array([pose_speaker.m[0][3], pose_speaker.m[1][3], pose_speaker.m[2][3]])

            except:
                return self.fallback_angle[0], self.fallback_angle[1], self.fallback_angle[2]

            if pose_head != False:

                # MYSTERIOUS PROBLEM: The Y and Z Axis are switched in the TrackerPose from openVR most of the times.
                mystery_flag = True #for testing debugging

                # STEP1: get the correct translation between head and speaker

                translation_head = np.array([pose_head.m[0][3], pose_head.m[1][3], pose_head.m[2][3]])

                if self.head_dimensions['ear_center'] is not None:
                    offset_x = self.head_dimensions['ear_center'][0] * np.array([pose_head.m[0][0], pose_head.m[1][0], pose_head.m[2][0]])
                    offset_y = self.head_dimensions['ear_center'][1] * np.array([pose_head.m[0][1], pose_head.m[1][1], pose_head.m[2][1]])
                    offset_z = self.head_dimensions['ear_center'][2] * np.array([pose_head.m[0][2], pose_head.m[1][2], pose_head.m[2][2]])

                    translation_head = translation_head + offset_x + offset_y + offset_z

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
                    up = np.array([0.0, 0.0, -1.0]) # i don´t know why, but y and z axis are switched somehow
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

        def get_tracker_data(self, only_tracker_1=False):

            #poseMatrix1 = []
            #poseMatrix2 = []

            pose = self.vr_system.getDeviceToAbsoluteTrackingPose(TrackingUniverseRawAndUncalibrated,
                                                                  1,
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
                if only_tracker_1:
                    poseMatrix1 = []
                return poseMatrix2, poseMatrix1
            else:
                if only_tracker_1:
                    poseMatrix2 = []
                return poseMatrix1, poseMatrix2

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

        def check_if_tracking_is_valid(self):
            if self.vr_system_initialized:
                if not self.trackers_switched:
                    return self.tracker1.isActive
                else:
                    return self.tracker2.isActive

        def set_tracking_mode(self, trackingmode):
            self.tracking_mode = trackingmode




