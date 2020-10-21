from tracker_manager import TrackerManager
import threading
from PyQt5 import QtCore
from measurement import Measurement
import numpy as np
import scipy.io
from grid_improving.grid_filling import angularDistance
import os
import pointrecommender
from datetime import date

class MeasurementController:

    def __init__(self):
        self.tracker = TrackerManager()
        self.measurement = Measurement()
        self.devices = self.measurement.get_names_of_defualt_devices()

        self.headmovement_trigger_counter = 0
        self.headmovement_ref_position = [0, 0, 1]
        self.auto_trigger_by_headmovement = False

        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.timer_callback)
        self.timer_interval_ms = 20
        self._timer.start(20)

        self.measurement_running_flag = False
        self.measurement_position = []
        self.measurement_valid = False
        self.measurement_history = np.array([])
        self.measurement_trigger = False
        self.reference_measurement_trigger = False

        self.gui_handle = []

        self.measurements = np.array([])
        self.raw_signals = np.array([])
        self.raw_feedbackloop = np.array([])

        self.measurements_reference = np.array([])
        self.raw_signals_reference = np.array([])
        self.raw_feedbackloop_reference = np.array([])

        self.positions = np.array([])

        self.numMeasurements = 0

        self.guidance_running = False
        self.recommended_points = {}
        self.point_recommender = pointrecommender.PointRecommender(self.tracker)

        today = date.today()
        self.current_date = today.strftime("%d_%m_%Y")



    def register_gui_handler(self, handle):
        self.gui_handle = handle

    def trigger_measurement(self):
        self.measurement_trigger = True

    def trigger_reference_measurement(self):
        self.reference_measurement_trigger = True

    def trigger_auto_measurement(self):
        self.auto_trigger_by_headmovement = True

    def stop_auto_measurement(self):
        self.auto_trigger_by_headmovement = False

    def timer_callback(self):
        if self.measurement_running_flag:

            # check for variance
            tolerance_angle = 2  # (degree)
            tolerance_radius = 0.1  # (meter)
            az, el, r = self.tracker.get_relative_position()
            variance = angularDistance(az, el, self.measurement_position[0],
                                       self.measurement_position[1]) * 180 / np.pi
            #print(variance)
            if (variance > tolerance_angle
                    or abs(r - self.measurement_position[2]) > tolerance_radius):
                self.measurement_valid = False
                self.tracker.trigger_haptic_impulse()

        else:
            # check for tracker status
            self.gui_handle.update_tracker_status(self.tracker.check_tracker_availability())

            if self.guidance_running:
                az, el, r = self.tracker.get_relative_position()
                if self.point_recommender.update_position(az, el):
                    self.measurement_trigger = True
                    self.gui_handle.vispy_canvas.meas_points.remove_recommended_points()


            # check for measurement triggers
            if self.tracker.checkForTriggerEvent() \
                    or self.measurement_trigger\
                    or self.check_for_trigger_by_headmovement():

                # start a measurement
                if not self.measurements.any():
                    self.tracker.calibrate_orientation()
                self.measurement_trigger = False
                az, el, r = self.tracker.get_relative_position()
                self.measurement_position = np.array([az, el, r])
                run_measurement = StartSingleMeasurementAsync(self)
                self.measurement_running_flag = True
                self.measurement_valid = True
                run_measurement.start()

            elif self.reference_measurement_trigger:
                # start reference measurement
                self.reference_measurement_trigger = False
                run_measurement = StartReferenceMeasurementAsync(self)
                run_measurement.start()

    def check_for_trigger_by_headmovement(self, ignore_autotriggermode = False):

        if not self.auto_trigger_by_headmovement and not ignore_autotriggermode:
            return False
        # this function has to be called by a periodic timer callback and checks if the user´s head has remained still for a defined time interval

        hold_still_interval_sec = 2
        hold_still_num_callbacks = hold_still_interval_sec*1000 / self.timer_interval_ms

        tolerance_angle = 2  # (degree)
        tolerance_radius = 0.1  # (meter)
        az, el, r = self.tracker.get_relative_position()
        variance = angularDistance(az, el, self.headmovement_ref_position[0],
                                   self.headmovement_ref_position[1]) * 180 / np.pi
        if (variance > tolerance_angle
                or abs(r - self.headmovement_ref_position[2]) > tolerance_radius):
            self.headmovement_trigger_counter = 0
            self.headmovement_ref_position = [az, el, r]
        else:
            self.headmovement_trigger_counter += 1
            if self.headmovement_trigger_counter > hold_still_num_callbacks:
                self.headmovement_trigger_counter = 0
                return True

        return False


    def done_measurement(self):

        self.measurement_running_flag = False

        #self.plotRecordings()

        if self.measurement_valid:
            self.measurement.play_sound(True)

            print("Measurement valid")

            [rec_l, rec_r, fb_loop] = self.measurement.get_recordings()
            self.gui_handle.plot_recordings(rec_l, rec_r, fb_loop)
            [ir_l, ir_r] = self.measurement.get_irs()
            self.gui_handle.plot_IRs(ir_l, ir_r)
            self.gui_handle.add_measurement_point(self.measurement_position[0], self.measurement_position[1])


            ir = np.array([[ir_l, ir_r]]).astype(np.float32)
            raw_rec = np.array([[rec_l, rec_r]]).astype(np.float32)
            raw_fb = np.array([[fb_loop]]).astype(np.float32)

            if self.measurements.any():
                self.measurements = np.concatenate((self.measurements, ir))
            else:
                self.measurements = ir

            if self.raw_signals.any():
                self.raw_signals = np.concatenate((self.raw_signals, raw_rec))
                self.raw_feedbackloop = np.concatenate((self.raw_feedbackloop, raw_fb))
            else:
                self.raw_signals = raw_rec
                self.raw_feedbackloop = raw_fb




            if self.positions.any():
                self.positions = np.concatenate((self.positions, self.measurement_position.reshape(1, 3)))
            else:
                self.positions = self.measurement_position.reshape(1, 3)

            export = {'rawRecorded': self.raw_signals,
                      'rawFeedbackLoop': self.raw_feedbackloop,
                      'dataIR': self.measurements,
                      'sourcePositions': self.positions,
                      'fs': 48000}

            filename = "measured_points_" + self.current_date + ".mat"
            filepath = os.path.join(self.output_path, filename)
            scipy.io.savemat(filepath, export)

            #enable point recommendation after 6 measurements
            self.numMeasurements += 1
            if self.numMeasurements >= 6:
                self.gui_handle.enable_point_recommendation()

        else:
            self.measurement.play_sound(False)
            print("ERROR, Measurement not valid")

    def done_measurement_reference(self):

        self.measurement.play_sound(True)

        [rec_l, rec_r, fb_loop] = self.measurement.get_recordings()
        self.gui_handle.plot_recordings(rec_l, rec_r, fb_loop)
        [ir_l, ir_r] = self.measurement.get_irs()
        self.gui_handle.plot_IRs(ir_l, np.zeros(np.size(ir_r)))

        self.gui_handle.add_reference_point()

        ir = np.array([[ir_l]]).astype(np.float32)
        raw = np.array([[rec_l]]).astype(np.float32)
        fb = np.array([[fb_loop]]).astype(np.float32)

        if self.measurements_reference.any():
            self.measurements_reference = np.concatenate((self.measurements_reference, ir))
            self.raw_signals_reference = np.concatenate((self.raw_signals_reference, raw))
            self.raw_feedbackloop_reference = np.concatenate((self.raw_feedbackloop_reference, fb))
        else:
            self.measurements_reference = ir
            self.raw_signals_reference = raw
            self.raw_feedbackloop_reference = fb

        export = {'ref_rawRecorded': self.raw_signals_reference,
                  'ref_rawFeedbackLoop': self.raw_feedbackloop_reference,
                  'referenceIR': self.measurements_reference,
                  'fs': 48000}

        filename = "reference_measurement_" + self.current_date + ".mat"
        filepath = os.path.join(self.output_path, filename)
        scipy.io.savemat(filepath, export)

    def set_output_path(self, path):
        self.output_path = path

    def recommend_points(self, num_points):

        if self.positions.any():

            self.clear_recommended_points()

            az, el = self.point_recommender.recommend_new_points(self.positions[:, 0:2], num_points)

            if abs(az) > 0 or abs(el) > 0:
                self.recommended_points['az'] = az
                self.recommended_points['el'] = el
                print("Recommend Point: " + str(az) + " | " + str(el))
                for i in range(np.size(az)):
                    self.gui_handle.vispy_canvas.meas_points.add_recommended_point(az[i], el[i])

                return az, el

        print("No point could be recommended")

    def clear_recommended_points(self):

        if bool(self.recommended_points):

            self.recommended_points = {}
            self.gui_handle.vispy_canvas.meas_points.remove_recommended_points()
            self.point_recommender.stop()
            self.guidance_running = False

    def start_guided_measurement(self):

        if bool(self.recommended_points):

            self.guidance_running = True

            # (currently fixed to only a single point)
            self.point_recommender.start_guided_measurement(self.recommended_points['az'][0], self.recommended_points['el'][0])



class StartSingleMeasurementAsync(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent

    def run(self):
        print("run")
        self.parent.measurement.single_measurement()
        print("stop")
        self.parent.done_measurement()

class StartReferenceMeasurementAsync(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent

    def run(self):
        print("run")
        self.parent.measurement.single_measurement()
        print("stop")
        self.parent.done_measurement_reference()