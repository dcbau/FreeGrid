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
    r_w = np.sqrt(abs(1+pose_mat[0][0]+pose_mat[1][1]+pose_mat[2][2]))/2
    r_x = (pose_mat[2][1]-pose_mat[1][2])/(4*r_w)
    r_y = (pose_mat[0][2]-pose_mat[2][0])/(4*r_w)
    r_z = (pose_mat[1][0]-pose_mat[0][1])/(4*r_w)

    return np.array([r_w,r_x,r_y,r_z])

def euler_from_quaternion(q):
    """
    Convert a quaternion (PyQuaternion object) into euler angles (yaw, pitch, roll)
    yaw is rotation around z in degree (counterclockwise)
    pitch is rotation around y in degree (counterclockwise)
    roll is rotation around x in degree (counterclockwise)
    """
    # TODO check if element index order is correct
    w, x, y, z = q.elements[0], q.elements[1], q.elements[2], q.elements[3]

    # https: // automaticaddison.com / how - to - convert - a - quaternion - into - euler - angles - in -python /
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = np.arctan2(t0, t1)

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_y = np.arcsin(t2)

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = np.arctan2(t3, t4)

    return np.rad2deg(yaw_z), np.rad2deg(pitch_y), np.rad2deg(roll_x)

def align_vecA_to_vecB(vector_a, vector_b):
    '''Returns a rotation matrix that aligns unit vector A to unit vector B'''
    v = np.cross(vector_a, vector_b)
    s = np.linalg.norm(v)
    c = np.dot(vector_a, vector_b)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    r = np.eye(3) + vx + np.dot(vx, vx) * (1 - c) / (s ** 2)

    return r

def project_vec_on_plane(vector_a, n_plane):
    '''Returns the projection of vector A on a plane represented by normal vector'''
    #source: https://www.geeksforgeeks.org/vector-projection-using-python/

    n_norm = np.sqrt(sum(n_plane ** 2))
    projection_on_normal = (np.dot(vector_a, n_plane) / n_norm ** 2) * n_plane

    return vector_a - projection_on_normal

class TrackerManager():


        def __init__(self):

            self.fallback_angle = np.array([0.0, 0.0, 1.0])
            self.trackers_switched = False
            self.counter = 0

            self.speaker_view = {
                'fwd': None,
                'up': None,
                'side': None
            }


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

            # initialize open VR
            try:
                self.vr_system = init(VRApplication_Background)
            except:
                return

            # get available trackers and controllers
            self.trackers = []
            self.controllers = []

            for deviceID in range(k_unMaxTrackedDeviceCount):
                dev_class = self.vr_system.getTrackedDeviceClass(deviceID)
                if dev_class == TrackedDeviceClass_GenericTracker:
                    self.trackers.append(Device(TrackedDeviceClass_GenericTracker, deviceID, True))
                elif dev_class == TrackedDeviceClass_Controller:
                    self.controllers.append(Device(TrackedDeviceClass_GenericTracker, deviceID, True))

            # experimental: if not enough trackers are connected, use controllers instead
            self.trackers.extend(self.controllers)

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

        def get_calibrated_position_from_pose(self, pose):
            '''Apply calibrated offset to the translation part of a pose matrix and return resulting translation vector'''
            translation_head = np.array([pose.m[0][3], pose.m[1][3], pose.m[2][3]])

            if self.head_dimensions['ear_center'] is not None:
                offset_x = self.head_dimensions['ear_center'][0] * np.array([pose.m[0][0], pose.m[1][0], pose.m[2][0]])
                offset_y = self.head_dimensions['ear_center'][1] * np.array([pose.m[0][1], pose.m[1][1], pose.m[2][1]])
                offset_z = self.head_dimensions['ear_center'][2] * np.array([pose.m[0][2], pose.m[1][2], pose.m[2][2]])

                translation_head = translation_head + offset_x + offset_y + offset_z

            return translation_head

        def calibrate_orientation_torso(self):
            # TODO add check that this is only done if everything else is calibrated
            try:
                pose_base, pose_relative = self.get_tracker_data()
                if pose_base == [] or pose_relative == []:
                    return False
            except:
                return False

            head_tracker = Quaternion(convert_to_quaternion(pose_base))
            torso_tracker = Quaternion(convert_to_quaternion(pose_relative))

            # HATO (Head-Above-Torso-Orientation)
            # assume: HATO_rotation * offset_rotation * TorsoTracker = HeadTracker
            # assume: HATO_rotation is zero
            # => offset_rotation = HeadTracker * inv(TorsoTracker)

            self.calibrationRotation_torso = torso_tracker.inverse * head_tracker

            return True

        def calibrate_orientation(self):

            try:
                pose_base, pose_relative = self.get_tracker_data()
                if pose_base == [] or pose_relative == []:
                    return False
            except:
                return False

            if self.head_dimensions['ear_center'] is not None and self.acoustical_center_pos is not None:

                translation_head = self.get_calibrated_position_from_pose(pose_base)

                # get vector pointing from head center to speaker center
                C_corr = self.acoustical_center_pos - translation_head

                # make the refinement vector
                C_corr = C_corr / np.linalg.norm(C_corr)
                vec_up = np.array([pose_relative[0][2], pose_relative[1][2], pose_relative[2][2]])
                C_corr = project_vec_on_plane(C_corr, vec_up)

                vec_forward = -np.array([pose_relative[0][1], pose_relative[1][1],
                                         pose_relative[2][1]])  # negative y-vector, determined empirically
                refine_R = align_vecA_to_vecB(vec_forward, C_corr)

                # apply to orientation components
                fwd = np.dot(refine_R, np.array([pose_relative[0][2], pose_relative[1][2], pose_relative[2][2]]))
                up = np.dot(refine_R, np.array([pose_relative[0][1], pose_relative[1][1], pose_relative[2][1]]))
                side = np.dot(refine_R, np.array([pose_relative[0][0], pose_relative[1][0], pose_relative[2][0]]))

                pose_relative[0][0] = side[0]
                pose_relative[1][0] = side[1]
                pose_relative[2][0] = side[2]
                pose_relative[0][1] = up[0]
                pose_relative[1][1] = up[1]
                pose_relative[2][1] = up[2]
                pose_relative[0][2] = fwd[0]
                pose_relative[1][2] = fwd[1]
                pose_relative[2][2] = fwd[2]

            else:
                self.calibrate_orientation_position_1 = pose_relative

            head_tracker = Quaternion(convert_to_quaternion(pose_base))
            reference_tracker = Quaternion(convert_to_quaternion(pose_relative))

            # assume: reference tracker(real head orientation) = head tracker  * offset
            self.calibrationRotation = head_tracker.inverse * reference_tracker

            # store inverted orientation to get speaker axis
            q1 = Quaternion(axis=[0, 0, 1], angle=np.pi)
            self.speaker_view['fwd'] = -np.array([pose_relative[0][2], pose_relative[1][2], pose_relative[2][2]])
            self.speaker_view['up'] = np.array([pose_relative[0][1], pose_relative[1][1], pose_relative[2][1]])
            self.speaker_view['side'] = -np.array([pose_relative[0][0], pose_relative[1][0], pose_relative[2][0]])

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

            # OSC tracking
            if self.tracking_mode == "OSC_direct":
                if self.osc_input_server is None:
                    self.osc_input_server = osc_input.OSCInputServer()
                    self.osc_input_server.start_listening()
                try:
                    angles = self.osc_input_server.get_current_angle()
                except:

                    return self.fallback_angle[0], self.fallback_angle[1], self.fallback_angle[2], 0, 0, 0

                return angles[0], angles[1], angles[2], 0, 0, 0

            # SteamVR tracking
            try:
                pose_head, pose_relative = self.get_tracker_data()
            except:
                # you produce an error, put you to return. no trial no nothing
                return self.fallback_angle[0], self.fallback_angle[1], self.fallback_angle[2], 0, 0, 0

            if self.acoustical_center_pos is not None:
                translation_speaker = self.acoustical_center_pos
            elif pose_relative !=[]:
                # if speaker is not calibrated yet, the live tracking speaker pose is used
                translation_speaker = np.array([pose_relative.m[0][3], pose_relative.m[1][3], pose_relative.m[2][3]])
            else:
                # right to return, right away
                return self.fallback_angle[0], self.fallback_angle[1], self.fallback_angle[2], 0, 0, 0

            if not pose_head:
                # believe it or not, return, right away
                return self.fallback_angle[0], self.fallback_angle[1], self.fallback_angle[2], 0, 0, 0

            # MYSTERIOUS PROBLEM: The Y and Z Axis are switched in the TrackerPose from openVR most of the times.
            mystery_flag = True #for testing debugging

            # STEP1: get the correct translation between head and speaker

            translation_head = self.get_calibrated_position_from_pose(pose_head)
            # get vector pointing from head center to speaker center
            transvec = translation_speaker - translation_head

            # STEP2: get the correct orientation of the head

            # get the head tracker rotation in quaternions
            head_rotation = Quaternion(convert_to_quaternion(pose_head))

            # apply calibrated rotation
            # assume: real head orientation = head tracker * offset
            rotation = head_rotation * self.calibrationRotation

            # make "new' direction vectors by rotating a normed set of orthogonal direction vectors
            if mystery_flag:
                side = rotation.rotate(np.array([1.0, 0.0, 0.0]))
                up = rotation.rotate(np.array([0.0, 0.0, -1.0])) # i don´t know why, but y and z axis are switched somehow
                fwd = rotation.rotate(np.array([0.0, 1.0, 0.0])) #
            else:
                side = rotation.rotate(np.array([1.0, 0.0, 0.0]))
                up = rotation.rotate(np.array([0.0, 1.0, 0.0]))
                fwd = rotation.rotate(np.array([0.0, 0.0, 1.0]))

            # STEP3: calculate direction vector to speaker relative to head coordinate system
            # (head coordinate system = side, up, fwd)

            source_direction_vector = np.array([np.inner(side, transvec), np.inner(up, transvec), np.inner(fwd, transvec)])
            radius = np.linalg.norm(source_direction_vector)
            source_direction_vector = source_direction_vector / radius

            # get spherical coordinates from direction vector
            az = np.rad2deg(np.arctan2(-source_direction_vector[0], -source_direction_vector[2]))
            if az < 0:
                az += 360

            el = np.rad2deg(np.arccos(-source_direction_vector[1]))
            el = el - 90

            source_direction = [az, el, radius]


            # speaker directivity
            transvec_2 = translation_head - translation_speaker
            speaker_directivity_vector = np.array([np.inner(self.speaker_view['side'], transvec_2), np.inner(self.speaker_view['up'], transvec_2), np.inner(self.speaker_view['fwd'], transvec_2)])
            radius2 = np.linalg.norm(speaker_directivity_vector)
            sp_dir_x = int(100*speaker_directivity_vector[0])
            sp_dir_y = int(100*speaker_directivity_vector[1])
            sp_dir_z = int(100*speaker_directivity_vector[2])

            speaker_directivity_vector = speaker_directivity_vector / radius2
            az2 = np.rad2deg(np.arctan2(-speaker_directivity_vector[0], -speaker_directivity_vector[2]))
            az2 = az2 % 360

            el2 = np.rad2deg(np.arccos(-speaker_directivity_vector[1]))
            el2 = el2 - 90

            speaker_directivity = [az2, el2, radius2]

            # HATO (Head-Above-Torso-Orientation)

            HATO_tracking_enabled = True
            if HATO_tracking_enabled and pose_relative:
                torso_rotation = Quaternion(convert_to_quaternion(pose_relative))

                # ASSUME:
                # (quaternion multiplication is noncommutative, rotation is logically applied from left to right)
                # (general rule: TotalRotation
                # H = HeadTracker rotation, T = TorsoTracker rotation, dR = delta rotation, dHATO = HATO rotation, dOS = offset rotation
                # https://math.stackexchange.com/questions/2124361/quaternions-multiplication-order-to-rotate-unrotate
                # H = T * dR
                #   => dR = T^-1 * H
                #
                # dR = dOS * dHATO !OR! dR = dHATO * dOS
                #   => dHATO = dOS^-1 * dR !OR! dHATO = dR * dOS^-1
                #
                # ==> dHATO = dOS^-1 * T^-1 * H !OR! dHATO = T^-1 * H * dOS^-1
                #
                # where dOS was calibrated in self.calibrate_orientation_torso() as:
                # dOS = T0^-1 * H0,  with T0 and H0 calibrated without HATO rotation

                # TODO check if quaternion mulitplication order is correct
                HATO_rotation_v1 = self.calibrationRotation_torso.inverse * torso_rotation.inverse * head_rotation
                HATO_rotation_v2 = torso_rotation.inverse * head_rotation * self.calibrationRotation_torso.inverse
                # TODO if it all works, move inversion to calibration step

                HATO_ypr_v1 = euler_from_quaternion(HATO_rotation_v1)
                HATO_ypr_v2 = euler_from_quaternion(HATO_rotation_v1)
                print(f'V1: {[round(a) for a in HATO_ypr_v1]}')
                print(f'V2: {[round(a) for a in HATO_ypr_v2]}')

                HATO_ypr = 0,0,0
            else:
                HATO_ypr = [np.nan, np.nan, np.nan]

            return {"SourceDirection": source_direction, "SpeakerDirectivity": speaker_directivity, "HATO": HATO_ypr}


        def get_tracker_data(self, only_tracker_1=False):
            'Will raise an error if communcation with SteamVR fails. Returns [] for an inactive/disconnected tracker'
            pose = self.vr_system.getDeviceToAbsoluteTrackingPose(TrackingUniverseRawAndUncalibrated,
                                                                  1,
                                                                  k_unMaxTrackedDeviceCount)
            pose_matrices = []

            for t in self.trackers:
                t_pose = pose[t.id]
                t.isAvailable = t_pose.bDeviceIsConnected
                t.isActive = t_pose.bPoseIsValid
                if t.isActive:
                    pose_matrices.append(t_pose.mDeviceToAbsoluteTracking)
                else:
                    pose_matrices.append([])

            if self.trackers_switched:
                pose_matrices[0], pose_matrices[1] = pose_matrices[1], pose_matrices[0]

            if only_tracker_1:
                pose_matrices[1] = []

            return pose_matrices[0], pose_matrices[1]

        def check_tracker_availability(self):
            tracker_status = {
                "tracker1": "Unavailable",
                "tracker2": "Unavailable"
            }
            if len(self.trackers) > 0:
                if self.trackers[0].isActive:
                    tracker_status['tracker1'] = "Tracking"
                elif self.trackers[0].isAvailable:
                    tracker_status['tracker1'] = "Available / Not tracking"

            if len(self.trackers) > 1:
                if self.trackers[1].isActive:
                    tracker_status['tracker1'] = "Tracking"
                elif self.trackers[1].isAvailable:
                    tracker_status['tracker1'] = "Available / Not tracking"

            return tracker_status


        def set_tracking_mode(self, trackingmode):
            self.tracking_mode = trackingmode




