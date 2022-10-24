from openvr import *
import time
import numpy as np
from pyquaternion import Quaternion


class Device:
    """
    Helper class to represent a trackable Vive device, like Controller or Tracker.
    """
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
    """ Get the orientation in quaterion format from a 4 by 4 pose matrix
    Args:
        pose_mat(array of float): 4 by 4 pose matrix as provided by OpenVR
    Returns:
        array of float: Orientation in Quaternion (W, X, Y, Z)
    """
    r_w = np.sqrt(abs(1+pose_mat[0][0]+pose_mat[1][1]+pose_mat[2][2]))/2
    r_x = (pose_mat[2][1]-pose_mat[1][2])/(4*r_w)
    r_y = (pose_mat[0][2]-pose_mat[2][0])/(4*r_w)
    r_z = (pose_mat[1][0]-pose_mat[0][1])/(4*r_w)

    return np.array([r_w, r_x, r_y, r_z])


class OpenVR_Tracker_Manager:
    """ Object to manage the OpenVR tracking and get head tracking data.

    An object of TrackerManager instantiates and holds a connection to SteamVR via the OpenVR API. The head tracking is
    realised with two Vive Trackers, where Tracker 1 is attached to the head and Tracker 2 is used as a reference and
    calibration tracker. After successfull instantiation, the tracked head orientation can be accessed by
    calling get_relative_position().

    How the head orientation is calculated:
        - By default (no calibration), the head orientation is defined as the position of Tracker 2 relative to the coordinate system of Tracker 1, expressed in spherical coordinates.
        - By calibrating the offset of Tracker 1 to the head center point (via calibrating left and right ear with calibrate_headdimensions()), the coordinate system origin of Tracker 1 is translated to the head center.
        - By calibrating the rotational offset of Tracker 1 to the view direction (via calibrate_orientation()), the coordinate system of Tracker 1 is rotated to match the view direction of the subject.
        - By calibrating the emitter position, the absolute position of Tracker 2 is stored and the stored position is further used instead of Tracker 2.


    Note:
        SteamVR needs to be running and trackers need to be connected at the time of object creation. The first tracker
        to be recognized by the system will be assigned to the head tracker role. The roles can be reversed via
        switch_trackers().
    """

    def __init__(self):

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

        self.emitter_pos = None
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
            if dev_class == TrackedDeviceClass_GenericTracker:
                if not hasattr(self, 'tracker1'):
                    if self.vr_system.isTrackedDeviceConnected(deviceID):
                        self.tracker1 = Device(TrackedDeviceClass_GenericTracker, deviceID)
                        self.tracker1.set_availability(True)
                elif not hasattr(self, 'tracker2'):
                    if self.vr_system.isTrackedDeviceConnected(deviceID):
                        self.tracker2 = Device(TrackedDeviceClass_GenericTracker, deviceID)
                        self.tracker2.set_availability(True)
            elif dev_class == TrackedDeviceClass_Controller:
                if not hasattr(self, 'controller1'):
                    self.controller1 = Device(TrackedDeviceClass_Controller, deviceID)
                    self.controller1.set_availability(self.vr_system.isTrackedDeviceConnected(deviceID))
                elif not hasattr(self, 'controller2'):
                    self.controller2 = Device(TrackedDeviceClass_Controller, deviceID)
                    self.controller2.set_availability(self.vr_system.isTrackedDeviceConnected(deviceID))

        self.calibrationRotation = Quaternion()
        self.calibrate_orientation()


    def calibrate_orientation(self):
        """
        Stores the inverted rotational offset from the reference/calibration-tracker (e.g. lying on a planar floor
        in view direction) to the head tracker.

        Returns:
             True if calibration was successful, False if an error occured
        """
        try:
            pose_base, pose_relative = self.get_tracker_data()
        except:
            return False

        head_tracker = Quaternion(convert_to_quaternion(pose_base))
        reference_tracker = Quaternion(convert_to_quaternion(pose_relative))

        self.calibrationRotation = head_tracker.inverse * reference_tracker

        return True


    def calibrate_headdimensions(self, pos, multiple_calls=True):
        """
            Stores the instantaneous position of the calibration tracker (translation relative to the head tracker)
            for the position specified by "pos". After 'left_ear' and 'right_ear' have been calibrated, the
            head center position is automatically calculated.

            Args:
                pos (str): 'left_ear' or 'right_ear' for ear positions and head center. 'left', 'right', 'front',
                    'back' for head dimensions, measured slightly above the ears
                multiple_calls (bool): if True, a series of position snapshots is taken over 2 seconds and averaged.
                    Increases position accuracy (default=True)

            Returns:
                 True if calibration was successful, False if an error occurs
        """
        if multiple_calls:
            num_calls = 40
            time_window_s = 1
            initial_sleep = 2
        else:
            num_calls = 1
            time_window_s = 0.1
            initial_sleep = 0.1

        sleep_interval = time_window_s / num_calls

        direction_vector_list = np.zeros([3, num_calls])
        valid_ids = np.full(num_calls, True, dtype=bool)

        time.sleep(initial_sleep)

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

        if not valid_ids.max():
            return False

        try:
            direction_vector = np.mean(direction_vector_list[:, valid_ids], axis=1)
        except:
            return False

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

    def calibrate_emitter_position(self):
        """
        When called, the current absolute position of the calibration tracker is stored as the emitter position.
        After successfull calibration, the calibrated emitter position is used for the reference point. If the emitter
        changes position after calibration, it can be simply re-calibrated with this function.

        Returns
            True if calibration was successful, False if an error occurs
        """
        try:
            pose_head, pose_acenter = self.get_tracker_data()
        except:
            return False

        self.emitter_pos = np.array([pose_acenter.m[0][3], pose_acenter.m[1][3], pose_acenter.m[2][3]])

        return True

    def switch_trackers(self):
        """Reverse head- and calibration tracker assignment.

        Per default, the first recognized Vive Tracker is assigned as the head tracker and the second Tracker is
        assigned as the calibration/reference tracker. A call to this function reverses the assignment
        """
        if hasattr(self, 'tracker1') and hasattr(self, 'tracker2'):
            self.tracker1, self.tracker2 = self.tracker2, self.tracker1

    def get_relative_position(self):
        """Get the current position of Tracker 2 (or calibrated position) relative to the local coordinate system of Tracker 1.

        Returns (list of float, or bool):
            Relative position in spherical coordinates [Azimuth (deg), Elevation (deg), Radius (m)], or False if an error
            occurs.
        """

        try:
            if self.emitter_pos is not None:
                # if the emitter position has been calibrated, the second tracker is obsolete for angle tracking
                pose_head, _ = self.get_tracker_data(only_tracker_1=True)
                translation_speaker = self.emitter_pos
            else:
                # if emitter is not calibrated yet, the position of the calibration/reference tracker is used
                pose_head, pose_speaker = self.get_tracker_data()
                translation_speaker = np.array([pose_speaker.m[0][3], pose_speaker.m[1][3], pose_speaker.m[2][3]])

        except:
            return False

        if not pose_head:
            return False

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

        # get the head tracker orientation in quaternions and apply calibrated rotation
        # to get actual head orientation
        head_rotation = Quaternion(*convert_to_quaternion(pose_head)) * self.calibrationRotation

        # make new direction vectors by rotating a normed set of orthogonal direction vectors
        # MYSTERIOUS PROBLEM: The Y and Z Axis are switched in the TrackerPose from openVR most of the times.
        mystery_flag = True  # for testing debugging
        if mystery_flag:
            head_side = head_rotation.rotate(np.array([1.0, 0.0, 0.0]))
            head_up = head_rotation.rotate(np.array([0.0, 0.0, -1.0])) # i don´t know why, but y and z axis are switched somehow
            head_fwd = head_rotation.rotate(np.array([0.0, 1.0, 0.0])) #
        else:
            head_side = head_rotation.rotate(np.array([1.0, 0.0, 0.0]))
            head_up = head_rotation.rotate(np.array([0.0, 1.0, 0.0]))
            head_fwd = head_rotation.rotate(np.array([0.0, 0.0, 1.0]))

        # STEP3: calculate direction vector to speaker relative to head coordinate system
        # (head coordinate system = side, up, fwd)
        direction_vector = np.array([np.inner(head_side, transvec), np.inner(head_up, transvec), np.inner(head_fwd, transvec)])
        radius = np.linalg.norm(direction_vector)
        direction_vector = direction_vector / radius

        # get spherical coordinates from direction vector
        az = np.rad2deg(np.arctan2(-direction_vector[0], -direction_vector[2]))
        if az < 0:
            az += 360
        el = np.rad2deg(np.arccos(-direction_vector[1]))
        el = el - 90

        return az, el, radius

    def update_tracker_status_from_pose(self, pose, tracker):
        tracker_pose = pose[tracker.id]
        if tracker_pose.bDeviceIsConnected:
            self.tracker1.isAvailable = True
            if tracker_pose.bPoseIsValid:
                tracker.isActive = True
            else:
                tracker.isActive = False
        else:
            tracker.isAvailable = False

    def get_tracker_data(self, only_tracker_1=False):
        """ Pull raw tracking data from OpenVR.

        Checks if trackers are available and data is valid, then returns the pose matrices.
        If an error is thrown inside this function, e.g. if openVR is not initialized, this function will not catch
        the error.

        Pose matrix is a numpy array of dimension [4, 4], first three columns hold the orthogonal X, Y and Z axis-vectors of the tracker,
        each column containing the x, y, z parts of one axis-vector. The last column holds the translation
        vector [tx, ty, tz]. Last row is empty.
        See https://github.com/osudrl/CassieVrControls/wiki/OpenVR-Quick-Start#the-position-vector for details
        [x1 y1 z1 tx]
        [x2 y2 z2 ty]
        [x3 y3 z3 tz]
        [-  -  -  -]

        Args:
            only_tracker_1 (bool, optional): If True, the second pose matrice is empty (default=False)

        Returns:
            List with two pose matrices (numpy.array, shape=[4, 4]) for both trackers
        """

        pose = self.vr_system.getDeviceToAbsoluteTrackingPose(TrackingUniverseRawAndUncalibrated,
                                                              1,
                                                              k_unMaxTrackedDeviceCount)
        self.update_tracker_status_from_pose(pose, self.tracker1)
        if self.tracker1.isActive:
            pose1 = pose[self.tracker1.id]
            pose_matrix1 = pose1.mDeviceToAbsoluteTracking

        self.update_tracker_status_from_pose(pose, self.tracker2)
        if self.tracker2.isActive:
            pose2 = pose[self.tracker2.id]
            pose_matrix2 = pose2.mDeviceToAbsoluteTracking
        else:
            pose_matrix2 = []

        if only_tracker_1:
            pose_matrix2 = []

        return pose_matrix1, pose_matrix2

    def check_tracker_availability(self):
        """
        Checks the state of the trackers and returns a dict with displayable information on the trackers.
        Returned information can have three states:
        - "Unavailable": Tracker not connected / recognized by SteamVR at all / SteamVR not running
        - "Available / Not tracking": Is or was connected, but not sending data, e.g. not visible or out of battery
        - "Tracking": Available and sending valid tracking data.

        Returns
            Dict with fields 'tracker1' and 'tracker2', containing info strings
        """
        tracker_status = {
            "tracker1": "Unavailable",
            "tracker2": "Unavailable"
        }
        if hasattr(self, 'tracker1'):
            if self.tracker1.isActive:
                tracker_status['tracker1'] = "Tracking"
            elif self.tracker1.isAvailable:
                tracker_status['tracker1'] = "Available / Not tracking"

        if hasattr(self, 'tracker2'):
            if self.tracker2.isActive:
                tracker_status['tracker2'] = "Tracking"
            elif self.tracker2.isAvailable:
                tracker_status['tracker2'] = "Available / Not tracking"

        return tracker_status

    def check_if_tracking_is_valid(self):
        """ Quick check if head tracker is sending valid data, returning True or False."""
        if self.vr_system_initialized:
            return self.tracker1.isActive







