import threading
from PyQt5 import QtCore
import numpy as np
import scipy.io
import scipy.signal.windows
import os
from datetime import date
from pythonosc import udp_client
import socket
import logging

from components.measurement_list import MeasurementListModel
from components.openvr_headtracking import OpenVR_Tracker_Manager
from components.dsp_helpers import make_HPCF, deconvolve, deconvolve_stereo
from components.measurement import Measurement
from components import angular_distance, pointrecommender, osc_input



logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',)


class MeasurementController:

    def __init__(self):
        self.headtracking = OpenVR_Tracker_Manager()
        self.measurement = Measurement()
        self.tracking_mode = "Vive"
        self.osc_input_server = None
        self.fallback_angle = np.array([0.0, 0.0, 1.0])

        self.headmovement_trigger_counter = 0
        self.headmovement_ref_position = [0, 0, 1]
        self.auto_trigger_by_headmovement = False

        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.callback_thread)
        self.timer_interval_ms = 20
        self._timer.start(20)

        self.measurement_running_flag = False
        self.measurement_tolerance_check = False
        self.measurement_position = []
        self.measurement_valid = False
        self.measurement_history = np.array([])
        self.measurement_trigger = False
        self.center_measurement_trigger = False

        self.process_and_export_lock = threading.Lock()

        self.gui_handle = []

        self.measurements = np.array([])
        self.raw_signals = np.array([])
        self.raw_feedbackloop = np.array([])

        self.measurements_center = np.array([])
        self.raw_signals_center = np.array([])
        self.raw_feedbackloop_center = np.array([])

        self.positions = np.array([])
        self.positions_list = MeasurementListModel()

        self.hp_irs = np.array([])
        self.raw_signals_hp = np.array([])
        self.raw_feedbackloop_hp = np.array([])
        self.numHPMeasurements = 0

        self.numMeasurements = 0

        self.guidance_running = False
        self.recommended_points = {}
        self.point_recommender = pointrecommender.PointRecommender(self.headtracking)
        #self.point_recommender.get_head_rotation_to_point(260, 40)

        today = date.today()
        self.current_date = today.strftime("%d_%m_%Y")

        self.send_osc_data = False
        self.osc_send_ip = '127.0.0.1'
        self.osc_send_port = 1337
        self.osc_send_address = '/guided_hrtfs/angle'
        self.osc_send_client = None

        self.fast_mode = False
        if self.fast_mode:
            self.measurement.sweep_parameters['sweeplength_sec'] = 0.05
            self.measurement.sweep_parameters['post_silence_sec'] = 0.5


    def register_gui_handler(self, handle):
        self.gui_handle = handle

    def trigger_measurement(self):
        if not self.measurement_running_flag:
            self.measurement_trigger = True

    def trigger_center_measurement(self):
        self.center_measurement_trigger = True

    def trigger_auto_measurement(self):
        self.gui_handle.autoMeasurementTriggerProgress.setVisible(True)
        self.auto_trigger_by_headmovement = True

    def stop_auto_measurement(self):
        self.gui_handle.autoMeasurementTriggerProgress.setVisible(False)
        self.auto_trigger_by_headmovement = False

    def set_tracking_mode(self, trackingmode):
        """ Set the tracking input mode. Currently only modes 'Vive' and 'OSC_direct' are supported"""
        self.tracking_mode = trackingmode

        if self.tracking_mode == "OSC_direct":
            if self.osc_input_server is None:
                self.osc_input_server = osc_input.OSCInputServer()
                self.osc_input_server.start_listening()

    def get_tracking_angles(self):
        if self.tracking_mode == "OSC_direct":
            try:
                angles = self.osc_input_server.get_current_angle()
            except:
                angles = self.fallback_angle

        if self.tracking_mode == "Vive":
            angles = self.headtracking.get_relative_position()
            if not angles:
                angles = self.fallback_angle

        return angles


    # main callback thread
    def callback_thread(self):

        #print(f'Active Threads: {threading.active_count()}, MRunning: {self.measurement_running_flag}')

        # check for tracker status
        if self.tracking_mode == "Vive":
            self.gui_handle.update_tracker_status(self.headtracking.check_tracker_availability())
        elif self.tracking_mode == "OSC_direct":
            self.gui_handle.set_osc_status(self.osc_input_server.get_osc_receive_status())

        az, el, r = self.get_tracking_angles()

        self.gui_handle.updateCurrentAngle(az, el, r)

        if self.send_osc_data:
            print(f"Sending OSC Data to {self.osc_send_address}")
            self.osc_send_client.send_message(self.osc_send_address, [az, el, r])



        if self.measurement_running_flag:
            if self.measurement_tolerance_check:
                # check for variance
                tolerance_angle = 2  # (degree)
                tolerance_radius = 0.1  # (meter)
                variance = angular_distance.angularDistance(az, el, self.measurement_position[0],
                                                            self.measurement_position[1])

                # widen up tolerance angle for extreme elevations, since they are uncomfortable to hold
                if abs(self.measurement_position[1]) > 45:
                    w = abs(self.measurement_position[1]) - 45
                    tolerance_angle += w / 4

                if (variance > tolerance_angle
                        or abs(r - self.measurement_position[2]) > tolerance_radius):
                    self.measurement_valid = False
                    if not self.fast_mode:
                        self.measurement.interrupt_measurement()

            return

        if self.guidance_running:
            if self.point_recommender.update_position(az, el):
                self.measurement_trigger = True
                self.gui_handle.remove_recommendation_point(None)

        # check for measurement triggers
        if self.measurement_trigger or self.check_for_trigger_by_headmovement(az, el, r):

            # start a measurement
            self.measurement_trigger = False
            self.measurement_position = np.array([az, el, r])
            #run_measurement = StartSingleMeasurementAsync(self)
            run_measurement = threading.Thread(target=self.hrir_measurement)
            self.measurement_running_flag = True
            self.measurement_tolerance_check = True
            self.measurement_valid = True
            run_measurement.start()

        elif self.center_measurement_trigger:
            # start center measurement
            self.center_measurement_trigger = False
            self.center_measurement()

    def check_for_trigger_by_headmovement(self, az, el, r, ignore_autotriggermode = False):

        # the warning should only be raised when auto_measurement, turning the warning off should always be possible
        # if self.tracker.vr_system_initialized:
        #     if not self.tracker.check_if_tracking_is_valid():
        #         self.gui_handle.warning_invalid_tracking(True)
        #     else:
        #         self.gui_handle.warning_invalid_tracking(False)
        #         return False

        if not self.auto_trigger_by_headmovement and not ignore_autotriggermode:
            return False

        # this function has to be called by a periodic timer callback and checks if the user´s head has remained still for a defined time interval

        hold_still_interval_sec = 1
        if self.fast_mode:
            hold_still_interval_sec = 0.5

        hold_still_num_callbacks = hold_still_interval_sec*1000 / self.timer_interval_ms

        tolerance_angle = 2  # (degree)
        tolerance_radius = 0.1  # (meter)
        variance = angular_distance.angularDistance(az, el, self.headmovement_ref_position[0],
                                                    self.headmovement_ref_position[1])
        if (variance > tolerance_angle
                or abs(r - self.headmovement_ref_position[2]) > tolerance_radius):
            self.headmovement_trigger_counter = 0
            self.headmovement_ref_position = [az, el, r]
        else:
            self.headmovement_trigger_counter += 1
            if self.headmovement_trigger_counter > hold_still_num_callbacks:
                self.headmovement_trigger_counter = 0
                self.gui_handle.autoMeasurementTriggerProgress.setRange(0,0)
                return True

        progress = self.headmovement_trigger_counter / hold_still_num_callbacks
        self.gui_handle.autoMeasurementTriggerProgress.setRange(0, 100)
        self.gui_handle.autoMeasurementTriggerProgress.setValue(int(progress * 100))

        return False


    def hrir_measurement(self):
        # this function is critical regarding threading the measurements. (Primarily I write this text for myself to illustrate the problem)
        # Every measurement is executed in an asynchronous thread. The basic procedure
        # would be to wait until every functino in hrir_measurement() has been executed, and at the end set self.measurement_running_flag
        # to false in order to signalize the main thread that the next measurement can be started. For speeding up
        # the automatic measurement process, some time-costly functions like deconvolution, plotting and saving to disk could be performed AFTER the
        # self.measurement_running_flag has been disabled. However, several problems arise from this:
        # - It is important that all the measurement data is retrieved from the measurement object BEFORE another measurement starts.
        #   measurement position data is shared across threads and would be overwritten if another measurement starts
        # - Plotting with matplotlib while an audio recording is ongoing causes significant audio glitches! Thus plotting should be avoided
        #   or done before the next measurement starts
        # - If the processes like deconvolution or saving to disk take longer than the next measurement to finish, the next
        #  measurement thread should wait until the last thread is finished. A simple lock should do the trick
        # So the basic schedule of this function should be:
        # 1. get all the data needed from the measurement and make a local copy (check threading.local())
        # 2. perform all steps that cannot be performed during another measurement, e.g. plotting
        # 3. disable measurement flag to start/enable the next measurement
        # 4. claim a lock. if lock is claimed, should wait in cue. the process should now be thread safe and be prepared to
        # 5. perform stuff like deconvolution and saving to disk
        # 6. release the lock
        # Some actions might need to be done when all measurement threads have finished (e.g. when thread count is 1). For example
        # plotting the IRs or enabling to look and modify the data table

        # a problem still persistent is that if more than one measurement is waiting for the lock to aquire, it is not guaranteed
        # that measurements are given the lock in the same order. This means that all waiting measurements are guaranteed
        # to be processed, but might be saved in the wrong ordering.
        # Given the rare propapility of this case and the non-critial effect, the simple lock should be sufficient. Replacing with a
        # queue object might be considered in the future

        try:
            [rec_l, rec_r, fb_loop] = self.measurement.single_measurement()
        except:
            self.measurement_valid = False

        self.measurement_tolerance_check = False

        if self.measurement_valid:

            if not self.fast_mode:
                self.measurement.play_sound(True)

            measurement_pos = self.measurement_position # make thread copy before new measurement starts and overwirtes self.measurement_position

            fs = self.measurement.get_samplerate()

            self.gui_handle.plot_recordings(rec_l, rec_r, fb_loop, fs, fb_loop_used=self.measurement.feedback_loop_used)

            self.measurement_running_flag = False

            # deconvolve and get IRs
            deconv_fc_hp = self.measurement.get_sweep_parameters()['f_start'] * 2
            deconv_fc_lp = 20000
            ir_l, ir_r = deconvolve_stereo(fb_loop, rec_l, rec_r, fs, lowpass=[deconv_fc_lp, 4, 2], highpass=[deconv_fc_hp, 4, 2])


            # wait for a previous measurement to finish storing and exporting
            self.process_and_export_lock.acquire()

            # add to data list
            self.positions_list.add_position(measurement_pos.reshape(1, 3))

            # plot
            #self.gui_handle.plot_IRs(ir_l, ir_r, self.measurement.get_samplerate())
            self.gui_handle.add_measurement_point(measurement_pos[0], measurement_pos[1])

            # store IRs (internally)
            ir = np.array([[ir_l, ir_r]]).astype(np.float32)
            raw_rec = np.array([[rec_l, rec_r]]).astype(np.float32)
            raw_fb = np.array([[fb_loop]]).astype(np.float32)

            if self.positions.any():
                self.measurements = np.concatenate((self.measurements, ir))
                self.raw_signals = np.concatenate((self.raw_signals, raw_rec))
                self.raw_feedbackloop = np.concatenate((self.raw_feedbackloop, raw_fb))
                self.positions = np.concatenate((self.positions, measurement_pos.reshape(1, 3)))

            else:
                self.measurements = ir
                self.raw_signals = raw_rec
                self.raw_feedbackloop = raw_fb
                self.positions = measurement_pos.reshape(1, 3)

            # export
            self.save_to_file()

            self.process_and_export_lock.release()

            # enable point recommendation after 6 measurements
            self.numMeasurements += 1
            if self.numMeasurements >= 6:
                self.gui_handle.enable_point_recommendation()

        else:
            self.measurement.play_sound(False)
            self.measurement_running_flag = False

    def save_to_file(self):

        headWidth = self.headtracking.head_dimensions['head_width']
        if headWidth is None:
            headWidth = "Not available"
        headLength = self.headtracking.head_dimensions['head_length']
        if headLength is None:
            headLength = "Not available"
        export = {'rawRecorded': self.raw_signals,
                  'rawFeedbackLoop': self.raw_feedbackloop,
                  'dataIR': self.measurements,
                  'sourcePositions': self.positions,
                  'fs': self.measurement.get_samplerate(),
                  'headWidth': headWidth,
                  'headLength': headLength,
                  'sweepParameters': self.measurement.sweep_parameters,
                  'feedback_loop': self.measurement.feedback_loop_used
        }

        scipy.io.savemat(self.get_filepath_for_irs(), export)

    def get_filepath_for_irs(self):

        session_name = self.gui_handle.session_name.text()
        filename = "measured_points_" + session_name + "_" + self.current_date + ".mat"
        filepath = os.path.join(self.output_path, filename)

        return filepath

    def center_measurement(self):

        [rec_center, _, fb_loop] = self.measurement.single_measurement()

        self.measurement.play_sound(True)

        self.gui_handle.plot_recordings(rec_center, None, fb_loop, self.measurement.get_samplerate())

        fs = self.measurement.get_samplerate()
        deconv_fc_hp = self.measurement.get_sweep_parameters()['f_start'] * 2
        deconv_fc_lp = 20000
        ir_center = deconvolve(fb_loop, rec_center, fs, lowpass=[deconv_fc_lp, 4, 2], highpass=[deconv_fc_hp, 4, 2])

        self.gui_handle.plot_IRs(ir_center, None, self.measurement.get_samplerate())

        self.gui_handle.add_center_point()

        ir = np.array([[ir_center]]).astype(np.float32)
        raw = np.array([[rec_center]]).astype(np.float32)
        fb = np.array([[fb_loop]]).astype(np.float32)

        if self.measurements_center.any():
            self.measurements_center = np.concatenate((self.measurements_center, ir))
            self.raw_signals_center = np.concatenate((self.raw_signals_center, raw))
            self.raw_feedbackloop_center = np.concatenate((self.raw_feedbackloop_center, fb))
        else:
            self.measurements_center = ir
            self.raw_signals_center = raw
            self.raw_feedbackloop_center = fb

        export = {'center_rawRecorded': self.raw_signals_center,
                  'center_rawFeedbackLoop': self.raw_feedbackloop_center,
                  'centerIR': self.measurements_center,
                  'fs': self.measurement.get_samplerate(),
                  'sweepParameters': self.measurement.sweep_parameters,
                  'feedback_loop': self.measurement.feedback_loop_used}


        session_name = self.gui_handle.session_name.text()
        filename = "center_measurement_" + session_name + "_" + self.current_date + ".mat"
        filepath = os.path.join(self.output_path, filename)
        scipy.io.savemat(filepath, export)

    def set_output_path(self, path):
        self.output_path = path

    def recommend_points(self, num_points=1):

        if self.positions.any():

            self.clear_recommended_points()

            az, el = self.point_recommender.recommend_new_points(self.positions[:, 0:2], num_points)

            #if abs(az) > 0 or abs(el) > 0:
            self.recommended_points['az'] = az
            self.recommended_points['el'] = el
            print("Recommend Point: " + str(az) + " | " + str(el))
            for i in range(np.size(az)):
                self.gui_handle.add_recommendation_point(az[i], el[i])

            return az, el

        print("No point could be recommended")

    def clear_recommended_points(self):

        if bool(self.recommended_points):

            self.recommended_points = {}
            self.gui_handle.remove_recommendation_point(None)
            self.point_recommender.stop()
            self.guidance_running = False

    def start_guided_measurement(self):

        if bool(self.recommended_points):

            self.guidance_running = True

            # (currently fixed to only a single point)
            self.point_recommender.start_guided_measurement(self.recommended_points['az'][0], self.recommended_points['el'][0])

    def delete_measurement(self, id):

        try:
            self.measurements = np.delete(self.measurements, id, 0)
            self.raw_signals = np.delete(self.raw_signals, id, 0)
            self.raw_feedbackloop = np.delete(self.raw_feedbackloop, id, 0)

            self.positions = np.delete(self.positions, id, 0)

            self.positions_list.remove_position(id)

            self.gui_handle.remove_measurement_point(id)


            self.save_to_file()

        except IndexError:
            print("Could not delete measurement: Invalid id")

    def delete_all_measurements(self):
        all_ids = np.arange(0, np.size(self.measurements, 0))

        self.measurements = np.array([])
        self.raw_signals = np.array([])
        self.raw_feedbackloop = np.array([])
        self.positions = np.array([])

        self.gui_handle.remove_measurement_point(None)
        self.positions_list.remove_position(all_ids)

    def hp_measurement(self):

        [rec_l, rec_r, fb_loop] = self.measurement.single_measurement(type='hpc')

        self.measurement.play_sound(True)

        fs = self.measurement.get_samplerate()

        deconv_fc_hp = 20
        deconv_fc_lp = 20000
        ir_l, ir_r = deconvolve_stereo(fb_loop, rec_l, rec_r, fs, lowpass=[deconv_fc_lp, 4, 2], highpass=[deconv_fc_hp, 4, 2])

        ir = np.array([[ir_l, ir_r]]).astype(np.float32)
        raw_rec = np.array([[rec_l, rec_r]]).astype(np.float32)
        raw_fb = np.array([[fb_loop]]).astype(np.float32)

        if self.hp_irs.any():
            self.hp_irs = np.concatenate((self.hp_irs, ir))
            self.raw_signals_hp = np.concatenate((self.raw_signals_hp, raw_rec))
            self.raw_feedbackloop_hp = np.concatenate((self.raw_feedbackloop_hp, raw_fb))
            self.numHPMeasurements += 1
        else:
            self.hp_irs = ir
            self.raw_signals_hp = raw_rec
            self.raw_feedbackloop_hp = raw_fb
            self.numHPMeasurements = 1

        self.estimate_hpcf()

        self.gui_handle.plot_hptf(self.hp_irs, fs=self.measurement.get_samplerate())
        self.gui_handle.hp_measurement_count.setText(f'Repetitions: {self.numHPMeasurements}')
        self.export_hp_measurement()

    def remove_all_hp_measurements(self):
        self.hp_irs = np.array([])
        self.raw_signals_hp = np.array([])
        self.raw_feedbackloop_hp = np.array([])

        self.gui_handle.plot_hptf(self.hp_irs, fs=self.measurement.get_samplerate())
        self.numHPMeasurements = 0

        self.gui_handle.hp_measurement_count.setText(" ")
        self.estimate_hpcf()


    def export_hp_measurement(self):
        try:
            beta = self.gui_handle.regularization_beta_box.value()
        except:
            print("Could not get beta value, not saving it")
            beta = 0.0

        export = {'hpir_rawRecorded': self.raw_signals_hp,
                  'hpir_rawFeedbackLoop': self.raw_feedbackloop_hp,
                  'hpir': self.hp_irs,
                  'beta': beta,
                  'fs': self.measurement.get_samplerate(),
                  'feedback_loop': self.measurement.feedback_loop_used}

        hp_name = self.gui_handle.headphone_name.text()
        filename = "headphone_ir_" + hp_name + "_" + self.current_date + ".mat"
        filepath = os.path.join(self.output_path, filename)
        scipy.io.savemat(filepath, export)

    def remove_hp_measurement(self):
        try:
            self.hp_irs = np.delete(self.hp_irs, -1, 0)
            self.raw_signals_hp = np.delete(self.raw_signals_hp, -1, 0)
            self.raw_feedbackloop_hp = np.delete(self.raw_feedbackloop_hp, -1, 0)
        except:
            return

        self.gui_handle.plot_hptf(self.hp_irs, fs=self.measurement.get_samplerate())
        self.numHPMeasurements -= 1

        if self.numHPMeasurements:
            self.gui_handle.hp_measurement_count.setText(f'Repetitions: {self.numHPMeasurements}')
        else:
            self.gui_handle.hp_measurement_count.setText(" ")

        # self.gui_handle.plot_hpc_recordings(rec_l, rec_r, fb_loop)

        self.export_hp_measurement()
        self.estimate_hpcf()

    def estimate_hpcf(self, beta_regularization=None):

        if beta_regularization is None:
            try:
                beta_regularization = self.gui_handle.regularization_beta_box.value()
            except:
                beta_regularization = 0.1

        if not self.hp_irs.any():
            self.gui_handle.plot_hpc_estimate(np.array([]), np.array([]))
            return

        Hcl, Hcr = make_HPCF(self.hp_irs, beta_regularization=beta_regularization, fs=self.measurement.get_samplerate())

        self.gui_handle.plot_hpc_estimate(Hcl, Hcr, self.measurement.get_samplerate())


    def start_osc_send(self, ip=None, port=None, address=None):
        if self.tracking_mode == "OSC_direct":
            return False

        if self.update_osc_parameters(ip, port, address):

            if self.osc_send_client is not None:
                del self.osc_send_client
            self.osc_send_client = udp_client.SimpleUDPClient(self.osc_send_ip, self.osc_send_port)

            self.send_osc_data = True
        else:
            return False

        return True


    def stop_osc_send(self):
        self.send_osc_data = False

    def update_osc_parameters(self, ip=None, port=None, address=None):
        if ip is not None:
            try:
                socket.inet_aton(ip)
            except OSError:
                print("Invalid IP Adress Format!")
                return False
            self.osc_send_ip = ip
        if port is not None:
            try:
                port = int(port)
            except ValueError:
                print("Invalid Port Format!")
                return False
            self.osc_send_port = port
        if address is not None:
            self.osc_send_address = address

        return True

    def get_osc_parameters(self):
        return self.osc_send_ip, self.osc_send_port, self.osc_send_address


