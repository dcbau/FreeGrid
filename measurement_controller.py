from tracker_manager import TrackerManager
import threading
from PyQt5 import QtCore
from measurement import Measurement
import numpy as np
import scipy.io
from grid_improving.grid_filling import angularDistance


class MeasurementController:

    def __init__(self):
        self.tracker = TrackerManager()
        self.measurement = Measurement()

        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.timer_callback)
        self._timer.start(20)

        self.measurement_running_flag = False
        self.measurement_position = []
        self.measurement_valid = False
        self.measurement_history = np.array([])
        self.measurement_trigger = False
        self.gui_handle = []

        self.measurements = np.array([])
        self.positions = np.array([])


    def register_gui_handler(self, handle):
        self.gui_handle = handle

    def trigger_measurement(self):
        self.measurement_trigger = True

    def timer_callback(self):
        if self.measurement_running_flag:

            # check for variance
            tolerance_angle = 1  # (degree)
            tolerance_radius = 0.1  # (meter)
            az, el, r = self.tracker.getRelativePosition()
            variance = angularDistance(az, el, self.measurement_position[0],
                                       self.measurement_position[1]) * 180 / np.pi
            if (variance > tolerance_angle
                    or abs(r - self.measurement_position[2]) > tolerance_radius):
                self.measurement_valid = False
                self.tracker.trigger_haptic_impulse()

        else:
            if self.tracker.checkForTriggerEvent() or self.measurement_trigger:

                # start a measurement
                self.measurement_trigger = False
                az, el, r = self.tracker.getRelativePosition()
                self.measurement_position = np.array([az, el, r])
                running_measurement = AsyncMeasurementThread(target_start=self.measurement.single_measurement, target_stop=self.done_measurement())
                self.measurement_running_flag = True
                self.measurement_valid = True
                running_measurement.start()


    def done_measurement(self):

        self.measurement_running_flag = False

        #self.plotRecordings()

        if self.measurement_valid:
            self.measurement.play_sound(True)
            self.
            print("Measurement valid")

            [rec_l, rec_r, fb_loop] = self.measurement.get_recordings()
            self.gui_handle.plot_recordings(rec_l, rec_r, fb_loop)
            [ir_l, ir_r] = self.measurement.get_irs()
            self.gui_handle.plot_IRs(ir_l, ir_r)
            self.gui_handle.add_measurement_point(self.measurement_position[0], self.measurement_position[1])


            ir = np.array([[ir_l, ir_r]]).astype(np.float32)

            if self.measurements.any():
                self.measurements = np.concatenate((self.measurements, ir))
            else:
                self.measurements = ir

            if self.positions.any():
                self.positions = np.concatenate((self.positions, self.measurement_position.reshape(1, 3)))
            else:
                self.positions = self.measurement_position.reshape(1, 3)

            export = {'dataIR': self.measurements, 'sourcePositions': self.positions}
            scipy.io.savemat("export_to_matlab", export)

            #
            # filename = "ir" + str(self.measurement_count) + "_az" + str(int(round(_az))) + "_el" + str(
            #     int(round(_el))) + ".wav"
            # wave.write(filename, 48000, ir)
            # self.measurement_count += 1
            #
            # if self.measurement_history.any():
            #     # if it is the first measurement, there´s nothing to append
            #     self.measurement_history = self.measurement_position
            # else:
            #     self.measurement_history = np.append(self.measurement_history, self.measurement_position)

        else:
            self.measurement.play_sound(False)
            print("ERROR, Measurement not valid")






class AsyncMeasurementThread(threading.Thread):
    def __init__(self, target_start, target_stop=None):
        self.start = target_start
        self.on_stop = target_stop
        threading.Thread.__init__(self)

    def run(self):
        print("run")

        self.start()
        if self.on_stop is not None:
            self.on_stop()