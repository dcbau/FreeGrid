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

            self.fallback_angle = np.array([0, 0, 1])

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
                        self.tracker1 = Device(TrackedDeviceClass_GenericTracker, deviceID)
                        self.tracker1.set_availability(self.vr_system.isTrackedDeviceConnected(deviceID))
                    elif (not hasattr(self, 'tracker2')):
                        self.tracker2 = Device(TrackedDeviceClass_GenericTracker, deviceID)
                        self.tracker2.set_availability(self.vr_system.isTrackedDeviceConnected(deviceID))
                elif(dev_class == TrackedDeviceClass_Controller):
                    if(not hasattr(self, 'controller1')):
                        self.controller1 = Device(TrackedDeviceClass_Controller, deviceID)
                        self.controller1.set_availability(self.vr_system.isTrackedDeviceConnected(deviceID))
                    elif (not hasattr(self, 'controller2')):
                        self.controller2 = Device(TrackedDeviceClass_Controller, deviceID)
                        self.controller2.set_availability(self.vr_system.isTrackedDeviceConnected(deviceID))


            if(hasattr(self, 'tracker1')):
                self.calibrationPose = self.calibrate()
                print("Has tracker one!")

            if (hasattr(self, 'tracker2')):

                print("Has tracker two!")

            if (hasattr(self, 'controller1')):
                print("Has controller 1!")

            if (hasattr(self, 'controller2')):
                print("Has controller 2!")

            self.calibrationRotation = Quaternion()
            self.calibrate()

            self.counter = 0




        def checkForTriggerEvent(self):

            #print("Check for Trigger Event")
            if (hasattr(self, 'controller1')):
                result, controllerState = self.vr_system.getControllerState(self.controller1.id)
                #print(controllerState.ulButtonPressed)
                if(bool(controllerState.ulButtonPressed >> 33 & 1)):
                    return True

            if (hasattr(self, 'controller2')):
                result, controllerState = self.vr_system.getControllerState(self.controller2.id)
                # print(controllerState.ulButtonPressed)
                if (bool(controllerState.ulButtonPressed >> 33 & 1)):
                    return True

            return False

        def trigger_haptic_impulse(self):
            if (hasattr(self, 'controller1')):
                self.vr_system.triggerHapticPulse(self.controller1.id, 1, 100)
            elif (hasattr(self, 'controller2')):
                self.vr_system.triggerHapticPulse(self.controller2.id, 1, 100)

        def calibrate(self):
            try:
                pose_base, pose_relative = self.getTrackerData()
            except:
               return



            head_tracker = Quaternion(convert_to_quaternion(pose_base))
            reference_tracker = Quaternion(convert_to_quaternion(pose_relative))

            self.calibrationRotation = head_tracker.inverse * reference_tracker


            print("Quaternion: ", self.calibrationRotation)
            print("Rotation Axis: ",  self.calibrationRotation.axis)
            print("Rotation Angle: ", self.calibrationRotation.degrees)



        def getViewVector(self):
            try:
                pose_base, pose_relative = self.getTrackerData()
            except:
                return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0


            z_pose = np.array([pose_base.m[0][2], pose_base.m[1][2], pose_base.m[2][2]])
            y_pose = np.array([pose_base.m[0][1], pose_base.m[1][1], pose_base.m[2][1]])
            x_pose = np.array([pose_base.m[0][0], pose_base.m[1][0], pose_base.m[2][0]])

            return x_pose, y_pose, z_pose, x_pose, y_pose, z_pose

            # get the base tracker rotation in quaternions

            head_tracker = Quaternion(convert_to_quaternion(pose_base))
            reference_tracker = Quaternion(convert_to_quaternion(pose_relative))


            # make "new' direction vectors by rotating a normed set of orthogonal direction vectors
            x = np.array([1.0, 0.0, 0.0])
            y = np.array([0.0, 1.0, 0.0])
            z = np.array([0.0, 0.0, 1.0])


            # apply calibrated rotation
            #rotation = reference_tracker


            #x_rot1 = rotation.rotate(x)
            #y_rot1 = rotation.rotate(y)
            #z_rot1 = rotation.rotate(z)


            # apply calibrated rotation


            # die rotation muss relativ zum tracker-koordinatensystem sein, nicht zum globalen!!
            # so funtionierts noch nicht aber der ansatz ist glaube ich gut

            #rotation_axis = self.calibrationRotation.axis
            #make rotation relative to tracker coordinate system
            #r = np.array([np.inner(x_rot1, rotation_axis), np.inner(y_rot1, rotation_axis), np.inner(z_rot1, rotation_axis)])
            #degrees = self.calibrationRotation.degrees
            #calibrationRotation  = Quaternion(axis=[r[0], r[1], r[2]], degrees=degrees)
            #print(calibrationRotation)

            rotation = head_tracker # self.calibrationRotation


            #rotation = calibrationRotation

            x_rot2 = rotation.rotate(x)
            y_rot2 = rotation.rotate(y)
            z_rot2 = rotation.rotate(z)
            #print(x_rot1, x_rot2)

            print(x_pose, y_pose, z_pose)

            return x_pose, y_pose, z_pose, x_rot2, y_rot2, z_rot2



        def getRelativePosition(self):

            try:
                pose_base, pose_relative = self.getTrackerData()
            except:
                try:
                    az, el, r = self.getRelativePositionSolo()
                    return az, el, r
                except:
                    #print("Execptoion")
                    #raise
                    return self.fallback_angle[0], self.fallback_angle[1], self.fallback_angle[2]
                #print("EXPECTOPOFIAEÖGOI")

            if (pose_base != False and pose_relative != False):


                # take direction vectors of tracker 2 as reference coordinate system
                # apply


                translation_base = np.array([pose_base.m[0][3], pose_base.m[1][3], pose_base.m[2][3]])
                translation_relative = np.array([pose_relative.m[0][3], pose_relative.m[1][3], pose_relative.m[2][3]])

                # offset from ears to tracker
                # true head center lies below the tracker (negative y/up direction) and shi, so we translate the pose matrix "down"
                offsetY = 0#-0.15 # approx 15cm
                offsetZ =  0#0.01 # needs to be tested
                offsetYvector = offsetY * np.array([pose_base.m[0][1], pose_base.m[1][1], pose_base.m[2][1]])
                offsetZvector = offsetZ * np.array([pose_base.m[0][2], pose_base.m[1][2], pose_base.m[2][2]])
                #translation_base = translation_base + offsetYvector + offsetZvector



                #transvec = np.array([pose_relative.m[0][3] - pose_base.m[0][3],
                #                     pose_relative.m[1][3] - pose_base.m[1][3],
                #                     pose_relative.m[2][3] - pose_base.m[2][3]])
                transvec = translation_relative - translation_base

                # get the base tracker rotation in quaternions

                fwd = np.array([pose_base.m[0][2], pose_base.m[1][2], pose_base.m[2][2]])
                up = np.array([pose_base.m[0][1], pose_base.m[1][1], pose_base.m[2][1]])
                side = np.array([pose_base.m[0][0], pose_base.m[1][0], pose_base.m[2][0]])

                r_w = np.sqrt(abs(1 + side[0] + up[1] + fwd[2])) / 2
                r_x = (up[2] - fwd[1]) / (4 * r_w)
                r_y = (fwd[0] - side[2]) / (4 * r_w)
                r_z = (side[1] - up[0]) / (4 * r_w)

                baseRotation = Quaternion(r_w, r_x, r_y, r_z)

                # apply calibrated rotation
                rotation = baseRotation* self.calibrationRotation

                # make "new' direction vectors by rotating a normed set of orthogonal direction vectors
                x = np.array([1.0, 0.0, 0.0])
                y = np.array([0.0, 0.0, -1.0]) # i don´t know why, but y and z axis are flipped somehow
                z = np.array([0.0, 1.0, 0.0]) #

                x_rot = rotation.rotate(x)
                y_rot = rotation.rotate(y)
                z_rot = rotation.rotate(z)




                #u = -np.array([pose_base.m[0][2], pose_base.m[1][2], pose_base.m[2][2]])
                #n = np.array([pose_base.m[0][1], pose_base.m[1][1], pose_base.m[2][1]])
                #v = np.array([pose_base.m[0][0], pose_base.m[1][0], pose_base.m[2][0]])

                #n = self.calibrationRotation.rotate(n)
                #u = self.calibrationRotation.rotate(u)
                #v = self.calibrationRotation.rotate(v)

                n = z_rot
                u = y_rot
                v = x_rot



                #transvec_projected = np.array([pose_base.m[0][2],
                #                               #pose_relative.m[1][3] - pose_base.m[1][3],
                #                               translation_relative[1] - translation_base[1],
                #                               pose_base.m[2][2]])

                #rxx = np.array([np.inner(v, transvec), np.inner(u, transvec_projected), np.inner(n, transvec)])
                # print("n=", n, "  u=", u, "  v=", v)
                r = np.array([np.inner(v, transvec), np.inner(u, transvec), np.inner(n, transvec)])

                r = r / np.linalg.norm(r)

                r2d = 180 / np.pi
                az = r2d * np.arctan2(r[0], -r[2])
                #print(r[0], r[2], az)
                radi = np.linalg.norm(r)
                #radixx = np.linalg.norm(rxx)
                #print(r[1])
                el = r2d * np.arccos(-r[1])
                el = el - 90

                if (az < 0):
                    az += 360
                #print("Az: ", az, "  El:", el)
                return az, el, radi



        def getTrackerData(self):

            # poseMatrix1 = []
            # poseMatrix2 = []

            if (hasattr(self, 'tracker1')):
                result, controllerState, trackedDevicePose = self.vr_system.getControllerStateWithPose(
                    TrackingUniverseRawAndUncalibrated, self.tracker1.id)
                self.vr_system.getDeviceToAbsoluteTrackingPose(TrackingUniverseRawAndUncalibrated, 0,
                                                               trackedDevicePose)
                if (trackedDevicePose.bDeviceIsConnected):
                    self.tracker1.isAvailable = True
                    if (trackedDevicePose.bPoseIsValid):
                        self.tracker1.isActive = True
                        poseMatrix1 = trackedDevicePose.mDeviceToAbsoluteTracking
                        #print("Angular Velocity", trackedDevicePose.vAngularVelocity)

            if (hasattr(self, 'tracker2')):
                result, controllerState, trackedDevicePose = self.vr_system.getControllerStateWithPose(
                    TrackingUniverseRawAndUncalibrated, self.tracker2.id)
                self.vr_system.getDeviceToAbsoluteTrackingPose(TrackingUniverseRawAndUncalibrated, 0,
                                                               trackedDevicePose)
                if (trackedDevicePose.bDeviceIsConnected):
                    self.tracker2.isAvailable = True
                    if (trackedDevicePose.bPoseIsValid):
                        self.tracker2.isActive = True
                        poseMatrix2 = trackedDevicePose.mDeviceToAbsoluteTracking

                # if ('poseMatrix1' in locals() and 'poseMatrix2' in locals()):
                return poseMatrix1, poseMatrix2
            # else:
            #    return False

        def set_angle_manually(self, azimuth, elevation):
            self.fallback_angle[0] = azimuth
            self.fallback_angle[1] = elevation



