# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets
from GUI.PicButton import PicButton
from GUI.vispyWidget import VispyCanvas, VispyWidget
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib

import os


class UiMainWindow(object):



    def setupUi(self, MainWindow, measurement_ref):
        MainWindow.setObjectName("MainWindow")

        self.measurement_ref = measurement_ref

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        #self.gridLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        MainWindow.resize(1100, 900)


        # VISPY WIDGET


        self.azimuthLabel = QtWidgets.QLabel("Az: ")
        self.azimuthLabel.setFont(QtGui.QFont("Arial", 24))
        self.azimuthLabel.setMaximumHeight(30)
        self.elevationLabel = QtWidgets.QLabel("El: ")
        self.elevationLabel.setFont(QtGui.QFont("Arial", 24))
        self.elevationLabel.setMaximumHeight(30)
        self.radiusLabel = QtWidgets.QLabel("Radius: ")
        self.radiusLabel.setFont(QtGui.QFont("Arial", 15))
        self.radiusLabel.setMaximumHeight(30)


        self.vpWidget = QtWidgets.QGroupBox("Virtual Speaker Position")
        self.vpWidget.setObjectName("vpWidget")
        self.vpWidget.setLayout(QtWidgets.QGridLayout())
        self.vpWidget.setMinimumSize(400, 400)

        self.vispy_canvas = VispyCanvas(measurement_ref, self)
        self.sliderTheta = QtWidgets.QSlider()
        self.sliderPhi = QtWidgets.QSlider()

        self.vpWidget.layout().addWidget(self.vispy_canvas.native, 0, 0, 4, 4)
        self.vpWidget.layout().addWidget(self.sliderTheta, 5, 0, 1, 4)
        self.vpWidget.layout().addWidget(self.sliderPhi, 0, 5, 4, 1)



        self.sliderTheta.setOrientation(QtCore.Qt.Horizontal)
        self.sliderTheta.setObjectName("sliderTheta")
        self.sliderTheta.valueChanged.connect(self.vispy_canvas.update_theta)

        self.sliderPhi.setOrientation(QtCore.Qt.Vertical)
        self.sliderPhi.setMinimum(-25)
        self.sliderPhi.setMaximum(25)
        self.sliderPhi.setValue(0)
        self.sliderPhi.setObjectName("sliderPhi")
        self.sliderPhi.valueChanged.connect(self.vispy_canvas.update_phi)


        self.vpWidget.layout().addWidget(self.azimuthLabel, 6, 1, 1, 1)
        self.vpWidget.layout().addWidget(self.elevationLabel, 6, 2, 1, 1)
        self.vpWidget.layout().addWidget(self.radiusLabel, 6, 3, 1, 1)




        # DEVICE STATUS WIDGET

        self.device_status_widget = QtWidgets.QGroupBox("Audio Device Status")
        devs = self.measurement_ref.devices

        self.label_out_exc = QtWidgets.QLabel(devs['out_excitation'])
        self.label_out_fb = QtWidgets.QLabel(devs['out_feedback'])
        self.label_in_left = QtWidgets.QLabel(devs['in_left'])
        self.label_in_right = QtWidgets.QLabel(devs['in_right'])
        self.label_in_fb = QtWidgets.QLabel(devs['in_feedback'])

        self.device_status_widget.setLayout(QtWidgets.QFormLayout())
        self.device_status_widget.layout().addRow(QtWidgets.QLabel("Output Excitation:"), self.label_out_exc)
        self.device_status_widget.layout().addRow(QtWidgets.QLabel("Output Feedback Loop:"), self.label_out_fb)
        self.device_status_widget.layout().addRow(QtWidgets.QLabel("Input Left Ear Mic:"), self.label_in_left)
        self.device_status_widget.layout().addRow(QtWidgets.QLabel("Input Right Ear Mic:"), self.label_in_right)
        self.device_status_widget.layout().addRow(QtWidgets.QLabel("Input Feedback Loop:"), self.label_in_fb)

        #self.device_status_widget.layout().setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.device_status_widget.setMaximumHeight(200)
        # TRACKER STATUS WIDGET

        self.tracker_status_widget = QtWidgets.QGroupBox("Vive Tracker Status")
        tracker_status = self.measurement_ref.tracker.check_tracker_availability()

        self.label_tr1 = QtWidgets.QLabel(tracker_status["tracker1"])
        self.label_tr2 = QtWidgets.QLabel(tracker_status["tracker2"])

        self.tracker_status_widget.setLayout(QtWidgets.QFormLayout())
        self.tracker_status_widget.layout().addRow(QtWidgets.QLabel("Tracker 1:"), self.label_tr1)
        self.tracker_status_widget.layout().addRow(QtWidgets.QLabel("Tracker 2:"), self.label_tr2)

        self.tracker_status_widget.setMaximumHeight(100)






        # TAB WIDGET

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
        self.tab_config.setLayout(QtWidgets.QVBoxLayout())
        self.tab_config.layout().setAlignment(QtCore.Qt.AlignCenter)
        self.tabWidget.addTab(self.tab_config, "")

        self.tab_measure = QtWidgets.QWidget()
        self.tab_measure.setEnabled(True)
        self.tab_measure.setObjectName("tab_measure")
        self.tab_measure.setLayout(QtWidgets.QVBoxLayout())
        self.tab_measure.layout().setAlignment(QtCore.Qt.AlignCenter)

        self.tabWidget.addTab(self.tab_measure, "")

        self.instructionsbox = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap("resources/tracker_setup.png")
        pixmap = pixmap.scaledToHeight(int(self.tab_config.height()), QtCore.Qt.SmoothTransformation)
        #pixmap = pixmap.scaledToWidth(500, QtCore.Qt.SmoothTransformation)
        self.instructionsbox.setPixmap(pixmap)
        #self.instructionsbox.setScaledContents(True)
        #self.instructionsbox.show()
        self.tab_config.layout().addWidget(self.instructionsbox)

        self.offsetbox = QtWidgets.QGroupBox()
        self.offsetbox.setLayout(QtWidgets.QFormLayout())

        self.offet_speaker_z = QtWidgets.QSpinBox()
        self.offet_speaker_y = QtWidgets.QSpinBox()
        self.offet_head_y = QtWidgets.QSpinBox()

        self.offet_speaker_z.setValue(self.measurement_ref.tracker.offset_cm['speaker_z'])
        self.offet_speaker_y.setValue(self.measurement_ref.tracker.offset_cm['speaker_y'])
        self.offet_head_y.setValue(self.measurement_ref.tracker.offset_cm['head_y'])

        self.offet_speaker_z.valueChanged.connect(self.set_offset_speaker_z)
        self.offet_speaker_y.valueChanged.connect(self.set_offset_speaker_y)
        self.offet_head_y.valueChanged.connect(self.set_offset_head_y)

        self.offsetbox.layout().addRow("Tracker - Speaker Z (cm): ", self.offet_speaker_z)
        self.offsetbox.layout().addRow("Tracker - Speaker Y (cm): ", self.offet_speaker_y)
        self.offsetbox.layout().addRow("Tracker - Head Y (cm): ", self.offet_head_y)

        self.tab_config.layout().addWidget(self.offsetbox)




        self.switchTrackersButton = QtWidgets.QPushButton(self.tab_measure)
        self.switchTrackersButton.setText("Switch Trackers")
        self.switchTrackersButton.setObjectName("switchTrackersButton")
        self.switchTrackersButton.setMaximumWidth(200)
        self.switchTrackersButton.clicked.connect(self.measurement_ref.tracker.switch_trackers)
        self.tab_config.layout().addWidget(self.switchTrackersButton)


        self.calibrateButton = QtWidgets.QPushButton(self.tab_measure)
        self.calibrateButton.setText("Calibrate")
        self.calibrateButton.setObjectName("calibrateButton")
        self.calibrateButton.clicked.connect(self.measurement_ref.tracker.calibrate)
        self.tab_config.layout().addWidget(self.calibrateButton)

        self.output_folder_box = QtWidgets.QGroupBox("Select output folder for measured data")
        self.output_folder_box.setLayout(QtWidgets.QHBoxLayout())
        path = os.getcwd()
        self.measurement_ref.set_output_path(path)

        self.output_folder_select = QtWidgets.QLineEdit()
        self.output_folder_select.setText(path)
        self.output_folder_box.layout().addWidget(self.output_folder_select)

        self.select_folder_button = QtWidgets.QPushButton()
        self.select_folder_button.setText("...")
        self.select_folder_button.clicked.connect(self.select_folder_dialog)
        self.output_folder_box.layout().addWidget(self.select_folder_button)

        self.tab_config.layout().addWidget(self.output_folder_box)

        self.azimuthBox = QtWidgets.QSpinBox()
        self.azimuthBox.setMaximum(359)
        self.azimuthBox.valueChanged.connect(self.manual_update_az)

        self.elevationBox = QtWidgets.QSpinBox()
        self.elevationBox.setMaximum(90)
        self.elevationBox.setMinimum(-90)
        self.elevationBox.valueChanged.connect(self.manual_update_el)

        self.manualAngleBox = QtWidgets.QGroupBox("Set angle manually")
        layout = QtWidgets.QFormLayout()
        layout.addRow(QtWidgets.QLabel("Azimuth °"), self.azimuthBox)
        layout.addRow(QtWidgets.QLabel("Elevation °"), self.elevationBox)
        self.manualAngleBox.setLayout(layout)
        self.tab_measure.layout().addWidget(self.manualAngleBox)

        self.startMeasurementGroupBox = QtWidgets.QGroupBox('Start Measurement')
        self.startMeasurementGroupBox.setLayout(QtWidgets.QHBoxLayout())

        self.referenceTriggerButton = QtWidgets.QPushButton('Reference Measurement')
        self.referenceTriggerButton.setObjectName("Reference Measurement")
        #self.referenceTriggerButton.setFixedSize(QtCore.QSize(100, 100))
        self.referenceTriggerButton.clicked.connect(self.measurement_ref.trigger_reference_measurement)

        #pixmap = QtGui.QPixmap("resources/start_button_x2.png")
        #pixmap_mouseover = QtGui.QPixmap("resources/start_button_x2_mouseover.png")
        #pixmap_pressed = QtGui.QPixmap("resources/start_button_x2_pressed.png")
        #self.measurementTriggerButton = PicButton(pixmap, pixmap_mouseover, pixmap_pressed)
        self.measurementTriggerButton = QtWidgets.QPushButton('Single Measurement')
        self.measurementTriggerButton.setEnabled(False)
        self.measurementTriggerButton.setObjectName("Single Measurement")
        self.measurementTriggerButton.setFixedSize(QtCore.QSize(200, 100))
        self.measurementTriggerButton.clicked.connect(self.measurement_ref.trigger_measurement)

        self.startMeasurementGroupBox.layout().addStretch()
        self.startMeasurementGroupBox.layout().addWidget(self.referenceTriggerButton)
        self.startMeasurementGroupBox.layout().addWidget(self.measurementTriggerButton)
        self.startMeasurementGroupBox.layout().addStretch()
        self.tab_measure.layout().addWidget(self.startMeasurementGroupBox)



        self.plotgroupbox = QtWidgets.QGroupBox('Measurement Plots')
        self.plotgroupbox.setLayout(QtWidgets.QVBoxLayout())

        self.plot_tab_widget = QtWidgets.QTabWidget()
        self.plot_tab_widget.setEnabled(True)
        self.plot_tab_widget.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.plot_tab_widget.setTabPosition(QtWidgets.QTabWidget.South)
        self.plot_tab_widget.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.plot_tab_widget.setIconSize(QtCore.QSize(32, 32))
        self.plot_tab_widget.setDocumentMode(True)
        self.plot_tab_widget.setTabsClosable(False)
        self.plot_tab_widget.setMovable(False)
        self.plot_tab_widget.setTabBarAutoHide(False)
        self.plot_tab_widget.setObjectName("plot_tab_widget")

        self.tab_rec = QtWidgets.QWidget()
        self.tab_rec.setEnabled(True)
        self.tab_rec.setObjectName("tab_rec")
        self.tab_rec.setLayout(QtWidgets.QVBoxLayout())
        self.plot_tab_widget.addTab(self.tab_rec, "")

        self.tab_ir = QtWidgets.QWidget()
        self.tab_ir.setEnabled(True)
        self.tab_ir.setObjectName("tab_ir")
        self.tab_ir.setLayout(QtWidgets.QVBoxLayout())
        self.plot_tab_widget.addTab(self.tab_ir, "")

        self.plot1 = Figure()
        self.plot1_canvas = FigureCanvas(self.plot1)
        self.tab_rec.layout().addWidget(self.plot1_canvas)

        self.plot2 = Figure()
        self.plot2_canvas = FigureCanvas(self.plot2)
        self.tab_ir.layout().addWidget(self.plot2_canvas)

        self.plotgroupbox.layout().addWidget(self.plot_tab_widget)
        self.tab_measure.layout().addWidget(self.plotgroupbox)




        self.gridLayout.addWidget(self.tabWidget, 0, 1, 3, 1)
        self.gridLayout.addWidget(self.vpWidget, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.device_status_widget, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.tracker_status_widget, 2, 0, 1, 1)

        self.gridLayout.setColumnStretch(0, 10)
        self.gridLayout.setColumnStretch(1, 10)


        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.measurement_ref.register_gui_handler(self)

        print('FINISH SETUP')





    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_config), _translate("MainWindow", "Configure"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_measure), _translate("MainWindow", "Measure"))
        self.plot_tab_widget.setTabText(self.plot_tab_widget.indexOf(self.tab_rec), _translate("MainWindow", "REC"))
        self.plot_tab_widget.setTabText(self.plot_tab_widget.indexOf(self.tab_ir), _translate("MainWindow", "IR"))


        # bounds = QtCore.QRect(self.tabWidget.geometry())
        # leftpane = QtCore.QRect(bounds)
        # leftpane.setWidth(bounds.width() / 2)
        # rightpane = leftpane.translated(bounds.width() / 2, 0)
        # leftpane.adjust(20, 20, -40, -40)
        # rightpane.adjust(20, 20, -40, -40)
        #
        # vispybox = QtCore.QRect(leftpane)
        # size = leftpane.width() if leftpane.width() < leftpane.height() else leftpane.height()
        # vispybox.setHeight(size)
        #
        # plotbox = QtCore.QRect(rightpane)
        # size = rightpane.width() if rightpane.width() < rightpane.height() else rightpane.height()
        # plotbox.setHeight(size)
        #
        # size = 80
        # self.pushButton.setGeometry(plotbox.x(),
        #                             plotbox.bottom() + 30,
        #                             80,
        #                             80)
        #
        # size = vispybox.width()*0.6
        # self.calibrateButton.setGeometry(vispybox.center().x() - size/2,
        #                                  self.sliderTheta.geometry().bottom(),
        #                                  size,
        #                                  40)
        # self.switchTrackersButton.setGeometry(vispybox.center().x() - size / 2,
        #                                       self.calibrateButton.geometry().bottom() + 5,
        #                                       size,
        #                                       40)
        # self.az_label.setGeometry(vispybox.x(),
        #                           self.switchTrackersButton.geometry().bottom() + 5,
        #                           80,
        #                           20)
        #
        # self.el_label.setGeometry(vispybox.x(),
        #                           self.az_label.geometry().bottom() + 5,
        #                           80,
        #                           20)
        #
        # self.azimuthBox.setGeometry(self.az_label.geometry().right() + 5,
        #                             self.az_label.geometry().y(),
        #                             80,
        #                             20)
        #
        # self.elevationBox.setGeometry(self.el_label.geometry().right() + 5,
        #                             self.el_label.geometry().y(),
        #                             80,
        #                             20)
        #
        # self.plot_tab_widget.setGeometry(plotbox)
        # self.plotWidget1.setGeometry(10,10, plotbox.width()-20, plotbox.height()-20)
        # self.plotWidget2.setGeometry(10,10, plotbox.width()-20, plotbox.height()-20)




    def manual_update_az(self):
        self.measurement_ref.tracker.fallback_angle[0] = self.azimuthBox.value()

    def manual_update_el(self):
        self.measurement_ref.tracker.fallback_angle[1] = self.elevationBox.value()

    def add_measurement_point(self, az, el):
        self.vispy_canvas.meas_points.add_point(az, el)

    def add_reference_point(self):
        self.measurementTriggerButton.setEnabled(True)
        self.vispy_canvas.meas_points.add_reference_measurement_point()

    def plot_recordings(self, rec_l, rec_r, fb_loop):
        matplotlib.rcParams.update({'font.size': 5})

        #[rec_l, rec_r, fb_loop] = self.measurement_ref.get_latest_recordings()
        self.plot1.clf()
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

    def plot_IRs(self, ir_l, ir_r):
        matplotlib.rcParams.update({'font.size': 5})

        # [rec_l, rec_r, fb_loop] = self.measurement_ref.get_latest_recordings()
        self.plot2.clf()
        ax1 = self.plot2.add_subplot(211)
        ax1.clear()
        ax1.plot(ir_l)

        ax2 = self.plot2.add_subplot(212)
        ax2.clear()
        ax2.plot(ir_r)

        self.plot2_canvas.draw()

    def update_tracker_status(self, status):
        self.label_tr1 = QtWidgets.QLabel(status["tracker1"])
        self.label_tr2 = QtWidgets.QLabel(status["tracker2"])

        if status["tracker1"] == "Tracking" and status["tracker2"] == "Tracking":
            self.manualAngleBox.setEnabled(False)
        else:
            self.manualAngleBox.setEnabled(True)

    def updateCurrentAngle(self, az, el, r):
        self.azimuthLabel.setText("Az: " + str(az) + "°")
        self.elevationLabel.setText("El: " + str(el) + "°")
        self.radiusLabel.setText("Radius: " + str(r) + "m")

    def set_offset_speaker_z(self):
        self.measurement_ref.tracker.offset_cm['speaker_z'] = self.offet_speaker_z.value()

    def set_offset_speaker_y(self):
        self.measurement_ref.tracker.offset_cm['speaker_y'] = self.offet_speaker_y.value()

    def set_offset_head_y(self):
        self.measurement_ref.tracker.offset_cm['head_y'] = self.offset_head_y.value()

    def select_folder_dialog(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self.centralwidget,
                                                          'Open Directory',
                                                          self.output_folder_select.text(),
                                                          QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)
        if path:
            self.output_folder_select.setText(path)
            self.measurement_ref.set_output_path(path)

