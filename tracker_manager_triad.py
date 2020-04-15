from ctypes import Array
from typing import Optional

#from openvr import *
import time
import numpy as np
#import pyshtools
from pyquaternion import Quaternion
import triad_openvr as vr



# def convert_to_quaternion(pose_mat):
#     # Per issue #2, adding a abs() so that sqrt only results in real numbers
#     r_w = np.sqrt(abs(1+pose_mat[0][0]+pose_mat[1][1]+pose_mat[2][2]))/2
#     r_x = (pose_mat[2][1]-pose_mat[1][2])/(4*r_w)
#     r_y = (pose_mat[0][2]-pose_mat[2][0])/(4*r_w)
#     r_z = (pose_mat[1][0]-pose_mat[0][1])/(4*r_w)
#
#     # left_x = m[0][0] = m0
#     # left_y = m[1][0] = m1
#     # left_z = m[2][0] = m2
#     # dummy =  m[3][0] = m3
#     #
#     # up_x = m[0][1] = m4
#     # up_y = m[1][1] = m5
#     # up_z = m[2][1] = m6
#     # dummy = m[3][1] = m7
#     #
#     # forward_x = m[0][2] = m8
#     # forward_y = m[1][2] = m9
#     # forward_z = m[2][2] = m10
#     # dummy = m[3][2] = m11
#     #
#     # translation_x = m[0][3] = m12
#     # translation_y = m[1][3] = m13
#     # translation_z = m[2][3] = m14
#     # dummy = m[3][3] = m15
#
#     return np.array([r_w,r_x,r_y,r_z])

class TrackerManager():


        def __init__(self):

            self.fallback_angle = np.array([0, 0, 1])

            # initialize open VR
            try:
                self.vr_system = vr.triad_openvr()
            except:
                print("Hell NO!")
                return

            #self.vr_system.print_discovered_objects()
            self.calibrationRotation = Quaternion()
            self.calibrate()

            self.counter = 0




        def checkForTriggerEvent(self):


            ##### NOT TESTED IN ANY WAY YET!!!!!!!!#################
            try:
                inputs = self.vr_system.devices['controller_1'].get_controller_inputs()
                if inputs['grip_button'] == True:
                    return True

                inputs = self.vr_system.devices['controller_2'].get_controller_inputs()
                if inputs['grip_button'] == True:
                    return True

            except:
                return False


        def trigger_haptic_impulse(self):
            try:
                self.vr_system.devices['controller_1'].trigger_haptic_pulse(100, 1)
                self.vr_system.devices['controller_2'].trigger_haptic_pulse(100, 1)
            except:
                return


        def calibrate(self):
            try:
                head_tracker =  self.vr_system.devices['tracker_1'].get_pose_quaternion()
                reference_tracker = self.vr_system.devices['tracker_2'].get_pose_quaternion()

            except:
                return

            head_tracker = Quaternion(head_tracker[3:7])
            reference_tracker = Quaternion(reference_tracker[3:7])
            self.calibrationRotation = head_tracker.inverse * reference_tracker


            print("Quaternion: ", self.calibrationRotation)
            print("Rotation Axis: ",  self.calibrationRotation.axis)
            print("Rotation Angle: ", self.calibrationRotation.degrees)


        def getViewVector(self):

            try:
                head_tracker =  self.vr_system.devices['tracker_1'].get_pose_quaternion()
                reference_tracker = self.vr_system.devices['tracker_2'].get_pose_quaternion()
                pose_base = self.vr_system.devices['tracker_1'].get_pose_matrix()

            except:
                return self.fallback_angle[0], self.fallback_angle[1], self.fallback_angle[2]



            translation_head_tracker = np.array([head_tracker[0], head_tracker[1], head_tracker[2]])
            translation_reference_tracker = np.array([reference_tracker[0], reference_tracker[1], reference_tracker[2]])

            #print(translation_base)
            # offset from ears to tracker
            # true head center lies below the tracker (negative y/up direction) and shi, so we translate the pose matrix "down"
            offsetY = 0#-0.15 # approx 15cm
            offsetZ =  0#0.01 # needs to be tested
            #offsetYvector = offsetY * np.array([pose_base.m[0][1], pose_base.m[1][1], pose_base.m[2][1]])
            #offsetZvector = offsetZ * np.array([pose_base.m[0][2], pose_base.m[1][2], pose_base.m[2][2]])
            #translation_base = translation_base + offsetYvector + offsetZvector



            #transvec = np.array([pose_relative.m[0][3] - pose_base.m[0][3],
            #                     pose_relative.m[1][3] - pose_base.m[1][3],
            #                     pose_relative.m[2][3] - pose_base.m[2][3]])
            transvec = translation_reference_tracker - translation_head_tracker

            z_pose = np.array([pose_base.m[0][2], pose_base.m[1][2], pose_base.m[2][2]])
            y_pose = np.array([pose_base.m[0][1], pose_base.m[1][1], pose_base.m[2][1]])
            x_pose = np.array([pose_base.m[0][0], pose_base.m[1][0], pose_base.m[2][0]])


            # get the base tracker rotation in quaternions

            head_tracker = Quaternion(head_tracker[3:7])
            reference_tracker = Quaternion(reference_tracker[3:7])


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
                base =  self.vr_system.devices['tracker_1'].get_pose_quaternion()
                relative = self.vr_system.devices['tracker_2'].get_pose_quaternion()
                pose_base = self.vr_system.devices['tracker_1'].get_pose_matrix()

            except:
                return self.fallback_angle[0], self.fallback_angle[1], self.fallback_angle[2]



            translation_base = np.array([base[0], base[1], base[2]])
            translation_relative = np.array([relative[0], relative[1], relative[2]])

            #print(translation_base)
            # offset from ears to tracker
            # true head center lies below the tracker (negative y/up direction) and shi, so we translate the pose matrix "down"
            offsetY = 0#-0.15 # approx 15cm
            offsetZ =  0#0.01 # needs to be tested
            #offsetYvector = offsetY * np.array([pose_base.m[0][1], pose_base.m[1][1], pose_base.m[2][1]])
            #offsetZvector = offsetZ * np.array([pose_base.m[0][2], pose_base.m[1][2], pose_base.m[2][2]])
            #translation_base = translation_base + offsetYvector + offsetZvector




            #transvec = np.array([pose_relative.m[0][3] - pose_base.m[0][3],
            #                     pose_relative.m[1][3] - pose_base.m[1][3],
            #                     pose_relative.m[2][3] - pose_base.m[2][3]])
            transvec = translation_relative - translation_base







            # get the base tracker rotation in quaternions

            base_quat = Quaternion(base[3:7])

            # apply calibrated rotation
            rotation =  self.calibrationRotation * base_quat

            # make "new' direction vectors by rotating a normed set of orthogonal direction vectors
            x = np.array([1.0, 0.0, 0.0])
            y = np.array([0.0, 0.0, -1.0])
            z = np.array([0.0, -1.0, 0.0])

            x_rot = rotation.rotate(x)
            y_rot = rotation.rotate(y)
            z_rot = rotation.rotate(z)

            n = z_rot
            u = y_rot
            v = x_rot

            #u = -np.array([pose_base.m[0][2], pose_base.m[1][2], pose_base.m[2][2]])
            #n = -np.array([pose_base.m[0][1], pose_base.m[1][1], pose_base.m[2][1]])
            #v = np.array([pose_base.m[0][0], pose_base.m[1][0], pose_base.m[2][0]])

            # this is the layout according to https://github.com/osudrl/CassieVrControls/wiki/OpenVR-Quick-Start
            # left_x = m[0][0] = m0
            # left_y = m[1][0] = m1
            # left_z = m[2][0] = m2
            # dummy =  m[3][0] = m3
            #
            # up_x = m[0][1] = m4
            # up_y = m[1][1] = m5
            # up_z = m[2][1] = m6
            # dummy = m[3][1] = m7
            #
            # forward_x = m[0][2] = m8
            # forward_y = m[1][2] = m9
            # forward_z = m[2][2] = m10
            # dummy = m[3][2] = m11
            #
            # translation_x = m[0][3] = m12
            # translation_y = m[1][3] = m13
            # translation_z = m[2][3] = m14
            # dummy = m[3][3] = m15

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

        def set_angle_manually(self, azimuth, elevation):
            self.fallback_angle[0] = azimuth
            self.fallback_angle[1] = elevation



