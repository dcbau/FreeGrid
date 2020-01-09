from ctypes import Array
from typing import Optional

from openvr import *
import time
import numpy as np


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



class TrackerManager():


        def __init__(self):

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
                print("Has tracker one!")

            if (hasattr(self, 'tracker2')):
                print("Has tracker two!")

            if (hasattr(self, 'controller1')):
                print("Has controller 1!")

            if (hasattr(self, 'controller2')):
                print("Has controller 2!")

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
                self.vr_system.triggerHapticPulse(self.controller1.id, 0, 10)
            elif (hasattr(self, 'controller2')):
                self.vr_system.triggerHapticPulse(self.controller2.id, 0, 10)


        def getRelativePosition(self):

            #print("Get Realtive Position")
            try:
                pose_base, pose_relative = self.getTrackerData()
            except:
                return 0, 0, 1
                print("EXPECTOPOFIAEÖGOI")

            if(pose_base != False and pose_relative != False):

                transvec = np.array([pose_relative.m[0][3] - pose_base.m[0][3],
                                     pose_relative.m[1][3] - pose_base.m[1][3],
                                     pose_relative.m[2][3] - pose_base.m[2][3]])
                n = np.array([pose_base.m[0][2], pose_base.m[1][2], pose_base.m[2][2]])
                u = np.array([pose_base.m[0][1], pose_base.m[1][1], pose_base.m[2][1]])
                v = np.array([pose_base.m[0][0], pose_base.m[1][0], pose_base.m[2][0]])
                #print("n=", n, "  u=", u, "  v=", v)
                r = np.array([np.inner(v, transvec), np.inner(u, transvec), np.inner(n, transvec)])
                #print("r= ", r)
                r2d = 180 / np.pi

                az = r2d * np.arctan2(r[0], -r[2])
                #print(r[0], r[2], az)
                radi = np.linalg.norm(r)
                el = r2d * np.arccos(r[1] / radi)

                if (az < 0):
                    az += 360

                return az, el, radi

        def getTrackerData(self):

            #poseMatrix1 = []
            #poseMatrix2 = []

            if(hasattr(self, 'tracker1')):
                result, controllerState, trackedDevicePose = self.vr_system.getControllerStateWithPose(TrackingUniverseRawAndUncalibrated, self.tracker1.id)
                self.vr_system.getDeviceToAbsoluteTrackingPose(TrackingUniverseRawAndUncalibrated, 0, trackedDevicePose)
                if (trackedDevicePose.bDeviceIsConnected):
                    self.tracker1.isAvailable = True
                    if(trackedDevicePose.bPoseIsValid):
                        self.tracker1.isActive = True
                        poseMatrix1 = trackedDevicePose.mDeviceToAbsoluteTracking

            if (hasattr(self, 'tracker2')):
                result, controllerState, trackedDevicePose = self.vr_system.getControllerStateWithPose(
                    TrackingUniverseRawAndUncalibrated, self.tracker2.id)
                self.vr_system.getDeviceToAbsoluteTrackingPose(TrackingUniverseRawAndUncalibrated, 0, trackedDevicePose)
                if (trackedDevicePose.bDeviceIsConnected):
                    self.tracker2.isAvailable = True
                    if (trackedDevicePose.bPoseIsValid):
                        self.tracker2.isActive = True
                        poseMatrix2 = trackedDevicePose.mDeviceToAbsoluteTracking


            #if ('poseMatrix1' in locals() and 'poseMatrix2' in locals()):
                return poseMatrix1, poseMatrix2
            #else:
            #    return False




