from measurement_list import MeasurementListModel
from tracking.tracker_manager import TrackerManager
import threading
from PyQt5 import QtCore
from measurement import Measurement
import numpy as np
import scipy.io
import scipy.signal.windows
from grid_improving import angular_distance
import os
from grid_improving import pointrecommender
from datetime import date
from pythonosc import udp_client
import socket


class MeasurementController:

    def __init__(self):
        self.tracker = TrackerManager()
        self.measurement = Measurement()

        self.headmovement_trigger_counter = 0
        self.headmovement_ref_position = [0, 0, 1]
        self.auto_trigger_by_headmovement = False

        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.callback_thread)
        self.timer_interval_ms = 20
        self._timer.start(20)

        self.measurement_running_flag = False
        self.measurement_position = []
        self.measurement_valid = False
        self.measurement_history = np.array([])
        self.measurement_trigger = False
        self.reference_measurement_trigger = False

        self.measurement_done_lock = threading.Lock()

        self.gui_handle = None

        self.measurements = np.array([])
        self.raw_signals = np.array([])
        self.raw_feedbackloop = np.array([])

        self.measurements_reference = np.array([])
        self.raw_signals_reference = np.array([])
        self.raw_feedbackloop_reference = np.array([])

        self.positions = np.array([])
        self.positions_list = MeasurementListModel()

        self.hp_irs = np.array([])
        self.raw_signals_hp = np.array([])
        self.raw_feedbackloop_hp = np.array([])
        self.numHPMeasurements = 0

        self.numMeasurements = 0

        self.guidance_running = False
        self.recommended_points = {}
        #self.point_recommender = pointrecommender.PointRecommender(self.tracker)
        #self.point_recommender.get_head_rotation_to_point(260, 40)

        today = date.today()
        self.current_date = today.strftime("%d_%m_%Y")

        self.send_osc_data = False
        self.osc_send_ip = '127.0.0.1'
        self.osc_send_port = 1337
        self.osc_send_address = '/guided_hrtfs/angle'
        self.osc_send_client = None

    def register_gui_handler(self, handle):
        self.gui_handle = handle

    def trigger_measurement(self):
        self.measurement_trigger = True

    def trigger_reference_measurement(self):
        self.reference_measurement_trigger = True

    def trigger_auto_measurement(self):
        self.gui_handle.autoMeasurementTriggerProgress.setVisible(True)
        self.auto_trigger_by_headmovement = True

    def stop_auto_measurement(self):
        self.gui_handle.autoMeasurementTriggerProgress.setVisible(False)
        self.auto_trigger_by_headmovement = False

    # main callback thread
    def callback_thread(self):

        # check for tracker status
        if self.gui_handle is not None:
            if self.tracker.tracking_mode == "Vive":
                self.gui_handle.update_tracker_status(self.tracker.check_tracker_availability())
            elif self.tracker.tracking_mode == "OSC_direct":
                self.gui_handle.set_osc_status(self.tracker.osc_input_server.get_osc_receive_status())

        if self.send_osc_data:
            az, el, r = self.tracker.get_relative_position()
            print(f"Sending OSC Data to {self.osc_send_address}")
            self.osc_send_client.send_message(self.osc_send_address, [az, el, r])





        if self.measurement_running_flag:

            # check for variance
            tolerance_angle = 2  # (degree)
            tolerance_radius = 0.1  # (meter)
            az, el, r = self.tracker.get_relative_position()
            variance = angular_distance.angularDistance(az, el, self.measurement_position[0],
                                       self.measurement_position[1])

            # widen up tolerance angle for extreme elevations, since they are uncomfortable to hold
            if abs(self.measurement_position[1]) > 45:
                w = abs(self.measurement_position[1]) - 45
                tolerance_angle += w/4

            if (variance > tolerance_angle
                    or abs(r - self.measurement_position[2]) > tolerance_radius):
                self.measurement_valid = False
                self.measurement.interrupt_measurement()

            return

        if self.guidance_running:
            az, el, r = self.tracker.get_relative_position()
            if self.point_recommender.update_position(az, el):
                self.measurement_trigger = True
                self.gui_handle.vispy_canvas.recommendation_points.clear_all_points()

        # check for measurement triggers
        if self.measurement_trigger or self.check_for_trigger_by_headmovement():

            # start a measurement
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
        hold_still_num_callbacks = hold_still_interval_sec*1000 / self.timer_interval_ms

        tolerance_angle = 2  # (degree)
        tolerance_radius = 0.1  # (meter)
        az, el, r = self.tracker.get_relative_position()
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
        self.gui_handle.autoMeasurementTriggerProgress.setValue(progress * 100)

        return False


    def done_hrir_measurement(self):

        if self.measurement_valid:

            # finish measurement by getting the recorded data
            self.measurement.play_sound(True)
            [rec_l, rec_r, fb_loop] = self.measurement.get_recordings()
            self.measurement_running_flag = False

            # deconvolve and get IRs
            [ir_l, ir_r] = self.measurement.get_irs(rec_l, rec_r, fb_loop)

            # wait for a previous measurement to finish storing and exporting
            self.measurement_done_lock.acquire()

            # add to data list
            self.positions_list.add_position(self.measurement_position.reshape(1, 3))

            # plot
            self.gui_handle.plot_recordings(rec_l, rec_r, fb_loop)
            self.gui_handle.plot_IRs(ir_l, ir_r)
            self.gui_handle.add_measurement_point(self.measurement_position[0], self.measurement_position[1])

            # store IRs (internally)
            ir = np.array([[ir_l, ir_r]]).astype(np.float32)
            raw_rec = np.array([[rec_l, rec_r]]).astype(np.float32)
            raw_fb = np.array([[fb_loop]]).astype(np.float32)

            if self.positions.any():
                self.measurements = np.concatenate((self.measurements, ir))
                self.raw_signals = np.concatenate((self.raw_signals, raw_rec))
                self.raw_feedbackloop = np.concatenate((self.raw_feedbackloop, raw_fb))
                self.positions = np.concatenate((self.positions, self.measurement_position.reshape(1, 3)))

            else:
                self.measurements = ir
                self.raw_signals = raw_rec
                self.raw_feedbackloop = raw_fb
                self.positions = self.measurement_position.reshape(1, 3)

            # export
            self.save_to_file()

            self.measurement_done_lock.release()


            # enable point recommendation after 6 measurements
            self.numMeasurements += 1
            if self.numMeasurements >= 3:
                self.gui_handle.enable_point_recommendation()

        else:
            self.measurement.play_sound(False)
            self.measurement_running_flag = False

    def save_to_file(self):

        headWidth = self.tracker.head_dimensions['head_width']
        if headWidth is None:
            headWidth = "Not available"
        headLength = self.tracker.head_dimensions['head_length']
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
                  'feedback_loop': self.measurement.audio_settings.feedback_loop_used
        }

        scipy.io.savemat(self.get_filepath_for_irs(), export)

    def get_filepath_for_irs(self):

        session_name = self.gui_handle.session_name.text()
        filename = "measured_points_" + session_name + "_" + self.current_date + ".mat"
        filepath = os.path.join(self.output_path, filename)

        return filepath

    def done_reference_measurement(self):

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
                  'fs': self.measurement.get_samplerate(),
                  'sweepParameters': self.measurement.sweep_parameters,
                  'feedback_loop': self.measurement.audio_settings.feedback_loop_used}


        session_name = self.gui_handle.session_name.text()
        filename = "reference_measurement_" + session_name + "_" + self.current_date + ".mat"
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
                self.gui_handle.vispy_canvas.recommendation_points.add_point(az[i], el[i])

            return az, el

        print("No point could be recommended")

    def clear_recommended_points(self):

        if bool(self.recommended_points):

            self.recommended_points = {}
            self.gui_handle.vispy_canvas.recommendation_points.clear_all_points()
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

            self.gui_handle.vispy_canvas.meas_points.remove_point(id)


            self.save_to_file()

        except IndexError:
            print("Could not delete measurement: Invalid id")

    def delete_all_measurements(self):
        all_ids = np.arange(0, np.size(self.measurements, 0))

        self.measurements = np.array([])
        self.raw_signals = np.array([])
        self.raw_feedbackloop = np.array([])
        self.positions = np.array([])

        self.gui_handle.vispy_canvas.meas_points.clear_all_points()
        self.positions_list.remove_position(all_ids)



    def hp_measurement(self):

        self.measurement.single_measurement(type='hpc')

        self.measurement.play_sound(True)

        [rec_l, rec_r, fb_loop] = self.measurement.get_recordings()

        [ir_l, ir_r] = self.measurement.get_irs()

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
                  'feedback_loop': self.measurement.audio_settings.feedback_loop_used}

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
        # algorithm taken in modified form from
        # https://github.com/spatialaudio/hptf-compensation-filters/blob/master/Calc_HpTF_compensation_filter.m
        # Copyright (c) 2016 Vera Erbes
        # licensed under MIT license

        if beta_regularization is None:
            try:
                beta_regularization = self.gui_handle.regularization_beta_box.value()
            except:
                beta_regularization = 0.4

        if not self.hp_irs.any():
            self.gui_handle.plot_hpc_estimate(np.array([]), np.array([]))
            return

        # parameters
        ####################
        filter_length = 4096
        window_length = 1024

        #regularization parameters
        fc_highshelf = 6000
        beta = beta_regularization

        M = np.size(self.hp_irs, 0)
        fs = self.measurement.get_samplerate()

        # algorithm
        #######################
        # create normalized working copies
        hl_raw = self.hp_irs[:, 0, :] / self.hp_irs.max()
        hr_raw = self.hp_irs[:, 1, :] / self.hp_irs.max()

        # approximate onsets and shift IRs to compensate delay
        onsets_l = np.argmax(hl_raw, axis=1)
        onsets_r = np.argmax(hr_raw, axis=1)

        for m in range(M):
            hl_raw[m, :] = np.roll(hl_raw[m, :], -(onsets_l[m]-50))
            hr_raw[m, :] = np.roll(hr_raw[m, :], -(onsets_r[m]-50))


        # window IRs and truncate
        win = scipy.signal.windows.blackmanharris(window_length)
        win[:int(window_length/2)] = 1
        win = np.pad(win, (0, filter_length-window_length))

        hl_win = hl_raw[:, : filter_length] * win
        hr_win = hr_raw[:, : filter_length] * win

        # complex mean of HpTFs
        Hl = np.fft.fft(hl_win, axis=1)
        Hr = np.fft.fft(hr_win, axis=1)

        Hl_mean = np.mean(Hl, axis=0)
        Hr_mean = np.mean(Hr, axis=0)

        # bandpass
        f_low = 20 / (fs/2)
        f_high = 20000 / (fs/2)
        stopatt = 60
        beta_kaiser = .1102*(stopatt-8.7)

        b = scipy.signal.firwin(filter_length,
                                [f_low, f_high],
                                pass_zero='bandpass',
                                window=('kaiser', beta_kaiser))
        BP = np.fft.fft(b)

        # regularization filter
        freq = np.array([0, 2000 / (fs/2), fc_highshelf / (fs/2), 1])
        G = np.array([-20, -20, 0, 0])
        g = 10**(G/20)
        b = scipy.signal.firwin2(51, freq, g)
        b = np.pad(b, (0, filter_length-np.size(b)))
        RF = np.fft.fft(b)

        # calculate complex filter
        Hcl = BP * np.conj(Hl_mean) / (Hl_mean * np.conj(Hl_mean) + beta * RF * np.conj(RF))
        Hcr = BP * np.conj(Hr_mean) / (Hr_mean * np.conj(Hr_mean) + beta * RF * np.conj(RF))

        self.gui_handle.plot_hpc_estimate(Hcl, Hcr)


    def start_osc_send(self, ip=None, port=None, address=None):
        if self.tracker.tracking_mode == "OSC_direct":
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














class StartSingleMeasurementAsync(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent

    def run(self):
        #print("run")

        self.parent.measurement.single_measurement()
        #print("stop")
        self.parent.done_hrir_measurement()

class StartReferenceMeasurementAsync(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent

    def run(self):
        #print("run")
        self.parent.measurement.single_measurement()
        #print("stop")
        self.parent.done_reference_measurement()