# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets
from GUI.PicButton import PicButton
from GUI.vispyWidget import VispyCanvas, VispyWidget
import threading
import numpy as np
from grid_improving.grid_filling import angularDistance
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib


class UiMainWindow(object):
    def setupUi(self, MainWindow, measurement_ref):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 700)

        self.measurement_ref = measurement_ref

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setEnabled(True)
        self.tabWidget.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.North)
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.tabWidget.setIconSize(QtCore.QSize(32, 32))
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setMovable(False)
        self.tabWidget.setTabBarAutoHide(False)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_config = QtWidgets.QWidget()
        self.tab_config.setEnabled(True)
        self.tab_config.setObjectName("tab_config")
        self.tabWidget.addTab(self.tab_config, "")
        self.tab_measure = QtWidgets.QWidget()
        self.tab_measure.setEnabled(True)
        self.tab_measure.setObjectName("tab_measure")

        self.vpWidget = VispyWidget(self.tab_measure)
        self.vpWidget.setObjectName("vpWidget")
        self.vpWidget.setLayout(QtWidgets.QVBoxLayout())
        self.vispy_canvas = VispyCanvas()
        self.vpWidget.layout().addWidget(self.vispy_canvas.native)

        self.sliderTheta = QtWidgets.QSlider(self.tab_measure)
        self.sliderTheta.setOrientation(QtCore.Qt.Horizontal)
        self.sliderTheta.setObjectName("sliderTheta")
        self.sliderTheta.valueChanged.connect(self.vispy_canvas.update_theta)

        self.sliderPhi = QtWidgets.QSlider(self.tab_measure)
        self.sliderPhi.setOrientation(QtCore.Qt.Vertical)
        self.sliderPhi.setMinimum(-25)
        self.sliderPhi.setMaximum(25)
        self.sliderPhi.setValue(0)
        self.sliderPhi.setObjectName("sliderPhi")
        self.sliderPhi.valueChanged.connect(self.vispy_canvas.update_phi)

        pixmap = QtGui.QPixmap("resources/start_button_x2.png")
        pixmap_mouseover = QtGui.QPixmap("resources/start_button_x2_mouseover.png")
        pixmap_pressed = QtGui.QPixmap("resources/start_button_x2_pressed.png")
        self.pushButton = PicButton(pixmap, pixmap_mouseover, pixmap_pressed, self.tab_measure)
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.trigger_measurement)

        self.calibrateButton = QtWidgets.QPushButton(self.tab_measure)
        self.calibrateButton.setText("Calibrate")
        self.calibrateButton.setObjectName("calibrateButton")
        self.calibrateButton.clicked.connect(self.vispy_canvas.tracker.calibrate)


        self.azimuthBox = QtWidgets.QSpinBox(self.tab_measure)
        self.azimuthBox.setGeometry(QtCore.QRect(440, 350, 80, 20))
        self.azimuthBox.setMaximum(359)
        self.azimuthBox.valueChanged.connect(self.manual_update_az)

        self.elevationBox = QtWidgets.QSpinBox(self.tab_measure)
        self.elevationBox.setGeometry(QtCore.QRect(440, 380, 80, 20))
        self.elevationBox.setMaximum(90)
        self.elevationBox.setMinimum(-90)
        self.elevationBox.valueChanged.connect(self.manual_update_el)

        self.az_label = QtWidgets.QLabel(self.tab_measure)
        self.az_label.setGeometry(520, 350, 100, 20)
        self.az_label.setText("Azimuth °")

        self.el_label = QtWidgets.QLabel(self.tab_measure)
        self.el_label.setGeometry(520, 380, 100, 20)
        self.el_label.setText("Elevation °")

        self.plotWidget = VispyWidget(self.tab_measure)
        self.plotWidget.setGeometry(QtCore.QRect(450, 10, 400, 300))
        self.plotWidget.setObjectName("plotWidget")
        self.plotWidget.setLayout(QtWidgets.QVBoxLayout())

        self.plot1 = Figure()
        self.plot1_canvas = FigureCanvas(self.plot1)
        self.plot2 = Figure()
        self.plot2_canvas = FigureCanvas(self.plot2)
        self.plot3 = Figure()
        self.plot3_canvas = FigureCanvas(self.plot3)
        self.plot4 = Figure()
        self.plot4_canvas = FigureCanvas(self.plot4)
        self.plotWidget.layout().addWidget(self.plot1_canvas)
        # self.plotWidget.layout().addWidget(self.plot2_canvas)
        # self.plotWidget.layout().addWidget(self.plot3_canvas)
        # self.plotWidget.layout().addWidget(self.plot4_canvas)

        self.tabWidget.addTab(self.tab_measure, "")
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 500, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.timer_callback)
        self._timer.start(20)

        self.measurement_running_flag = False
        self.measurement_position = []
        self.measurement_valid = False
        self.measurement_history = np.array([])
        self.mesurement_trigger = False

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_config), _translate("MainWindow", "Configure"))
        self.pushButton.setText(_translate("MainWindow", "PushButton"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_measure), _translate("MainWindow", "Measure"))

        self.vpWidget.setGeometry(QtCore.QRect(10, 10, 400, 400))

        self.sliderTheta.setGeometry(self.vpWidget.frameGeometry().x(),
                                     self.vpWidget.frameGeometry().bottom(),
                                     self.vpWidget.frameGeometry().width(),
                                     20)
        self.sliderPhi.setGeometry(self.vpWidget.frameGeometry().right(),
                                   self.vpWidget.frameGeometry().y(),
                                   20,
                                   self.vpWidget.frameGeometry().height())

        self.pushButton.setGeometry(QtCore.QRect(750, 350, 189 / 2, 187 / 2))

        self.calibrateButton.setGeometry(QtCore.QRect(650, 350, 50, 20))


    def manual_update_az(self):
        self.vispy_canvas.tracker.fallback_angle[0] = self.azimuthBox.value()

    def manual_update_el(self):
        self.vispy_canvas.tracker.fallback_angle[1] = self.elevationBox.value()

    def select_output_device(self, name):
        self.measurement_ref.set_output_device_by_name(name)

    def select_input_device(self, name):
        self.measurement_ref.set_input_device_by_name(name)

    def trigger_measurement(self):
        self.mesurement_trigger = True

    def timer_callback(self):
        if (self.measurement_running_flag == True):
            # check for variance
            tolerance_angle = 1  # (degree)
            tolerance_radius = 0.1  # (meter)
            az, el, r = self.vispy_canvas.tracker.getRelativePosition()
            variance = angularDistance(az, el, self.measurement_position[0], self.measurement_position[1]) * 180 / np.pi
            if (variance > tolerance_angle
                    or abs(r - self.measurement_position[2]) > tolerance_radius):
                self.measurement_valid = False
                self.vispy_canvas.tracker.trigger_haptic_impulse()


        else:
            if (self.vispy_canvas.tracker.checkForTriggerEvent() or self.mesurement_trigger):
                self.mesurement_trigger = False
                az, el, r = self.vispy_canvas.tracker.getRelativePosition()
                self.measurement_position = np.array([az, el, r])
                t1 = MeasurementHelperThread(target=self.measurement_ref.single_measurement, ref=self)
                self.measurement_running_flag = True
                self.measurement_valid = True
                t1.start()

    def stop_measurement(self):

        self.measurement_running_flag = False

        self.plotRecordings()

        self.measurement_ref.save_single_measurement(self.measurement_valid,
                                                     self.measurement_position[0],
                                                     self.measurement_position[1],
                                                     self.measurement_position[2])

        if self.measurement_valid:
            self.vispy_canvas.meas_points.add_point(self.measurement_position[0], self.measurement_position[1])
            print("Measurement valid")
        else:
            print("ERROR, Measurement not valid")

        if self.measurement_history.any():
            # if it is the first measurement, there´s nothing to append
            self.measurement_history = self.measurement_position
        else:
            self.measurement_history = np.append(self.measurement_history, self.measurement_position)

    def plotRecordings(self):
        matplotlib.rcParams.update({'font.size': 5})

        [rec_l, rec_r, fb_loop] = self.measurement_ref.get_recordings()
        ax1 = self.plot1.add_subplot(311)
        ax1.clear()
        ax1.plot(rec_l)

        ax2 = self.plot1.add_subplot(312)
        ax2.clear()
        ax2.plot(rec_r)

        ax3 = self.plot1.add_subplot(313)
        ax3.clear()
        ax3.plot(fb_loop)
        self.plot1_canvas.draw()


class MeasurementHelperThread(threading.Thread):
    def __init__(self, target, ref):
        self._starget = target
        self._ref = ref
        threading.Thread.__init__(self)

    def run(self):
        print("run")

        self._starget()
        self._ref.stop_measurement()
