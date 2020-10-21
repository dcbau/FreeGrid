# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets
from GUI.PicButton import PicButton
from GUI.vispyWidget import VispyCanvas, VispyWidget
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import pointrecommender

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

        self.myMainWindow = MainWindow

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

        self.tab_data = QtWidgets.QWidget()
        self.tab_data.setEnabled(True)
        self.tab_data.setObjectName("tab_data")
        self.tab_data.setLayout(QtWidgets.QVBoxLayout())
        self.tab_data.layout().setAlignment(QtCore.Qt.AlignCenter)
        self.tabWidget.addTab(self.tab_data, "")



        ## CONFIGURE TAB
        #############################

        self.dlg = InstructionsDialogBox()
        self.show_instructions_button = QtWidgets.QPushButton(self.tab_measure)
        self.show_instructions_button.setText("Show Calibration Instructions")
        self.show_instructions_button.clicked.connect(self.dlg.show)
        self.show_instructions_button.setMaximumWidth(200)
        self.tab_config.layout().addWidget(self.show_instructions_button)


        self.switchTrackersButton = QtWidgets.QPushButton(self.tab_measure)
        self.switchTrackersButton.setText("Switch Trackers")
        self.switchTrackersButton.setObjectName("switchTrackersButton")
        self.switchTrackersButton.setMaximumWidth(200)
        self.switchTrackersButton.clicked.connect(self.measurement_ref.tracker.switch_trackers)
        self.tab_config.layout().addWidget(self.switchTrackersButton)

        #self.spacer = QtWidgets.QSpacerItem(20, 50, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        #self.tab_config.layout().addWidget(QtWidgets.QLabel(""))

        self.offset_configuration_box = QtWidgets.QGroupBox("Source/Receiver Calibration")
        self.offset_configuration_box.setLayout(QtWidgets.QVBoxLayout())
        self.offset_configuration_box.setMaximumHeight(250)

        self.tab_config.layout().addWidget(self.offset_configuration_box)

        self.offset_configuration_widget = QtWidgets.QTabWidget()
        self.offset_configuration_box.layout().addWidget(self.offset_configuration_widget)
        self.offset_configuration_widget.setEnabled(True)
        self.offset_configuration_widget.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.offset_configuration_widget.setTabPosition(QtWidgets.QTabWidget.North)
        self.offset_configuration_widget.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.offset_configuration_widget.setIconSize(QtCore.QSize(32, 32))
        self.offset_configuration_widget.setDocumentMode(True)
        self.offset_configuration_widget.setTabsClosable(False)
        self.offset_configuration_widget.setMovable(False)
        self.offset_configuration_widget.setTabBarAutoHide(False)


        self.manual_offsetbox = QtWidgets.QGroupBox()
        self.manual_offsetbox.setLayout(QtWidgets.QFormLayout())

        self.offset_speaker_z = QtWidgets.QSpinBox()
        self.offset_speaker_y = QtWidgets.QSpinBox()
        self.offset_head_y = QtWidgets.QSpinBox()

        self.offset_speaker_z.setValue(self.measurement_ref.tracker.offset_cm['speaker_z'])
        self.offset_speaker_y.setValue(self.measurement_ref.tracker.offset_cm['speaker_y'])
        self.offset_head_y.setValue(self.measurement_ref.tracker.offset_cm['head_y'])

        self.offset_speaker_z.valueChanged.connect(self.set_offset_speaker_z)
        self.offset_speaker_y.valueChanged.connect(self.set_offset_speaker_y)
        self.offset_head_y.valueChanged.connect(self.set_offset_head_y)

        self.manual_offsetbox.layout().addRow("Tracker - Speaker Z (cm): ", self.offset_speaker_z)
        self.manual_offsetbox.layout().addRow("Tracker - Speaker Y (cm): ", self.offset_speaker_y)
        self.manual_offsetbox.layout().addRow("Tracker - Head Y (cm): ", self.offset_head_y)

        self.calibrated_offsetbox = QtWidgets.QGroupBox()
        self.calibrated_offsetbox.setLayout(QtWidgets.QFormLayout())
        self.calibrated_offsetbox.layout().setLabelAlignment(QtCore.Qt.AlignLeft)

        self.calibrate_ear_left = QtWidgets.QPushButton(text='Calibrate Left Ear')
        self.calibrate_ear_left.clicked.connect(self.trigger_left_ear_calibration)
        self.calibrate_ear_left_label = QtWidgets.QLabel(text="Uncalibrated, using manual offset")
        self.calibrated_offsetbox.layout().addRow(self.calibrate_ear_left, self.calibrate_ear_left_label)

        self.calibrate_ear_right = QtWidgets.QPushButton(text='Calibrate Right Ear')
        self.calibrate_ear_right.clicked.connect(self.trigger_right_ear_calibration)
        self.calibrate_ear_right_label = QtWidgets.QLabel(text="Uncalibrated, using manual offset")
        self.calibrated_offsetbox.layout().addRow(self.calibrate_ear_right, self.calibrate_ear_right_label)

        self.head_diameter_label = QtWidgets.QLabel(text="")
        self.calibrated_offsetbox.layout().addRow(self.head_diameter_label)

        self.calibrate_acoustical_center = QtWidgets.QPushButton(text='Calibrate Acoustical \nCentre of Speaker')
        self.calibrate_acoustical_center.clicked.connect(self.trigger_acoustical_centre_calibration)
        self.calibrate_acoustical_center_label = QtWidgets.QLabel(text="Uncalibrated, using manual offset")
        self.calibrated_offsetbox.layout().addRow(self.calibrate_acoustical_center, self.calibrate_acoustical_center_label)

        self.offset_configuration_widget.addTab(self.calibrated_offsetbox, "Calibrated Offset")
        self.offset_configuration_widget.addTab(self.manual_offsetbox, "Manual Offset")






        self.anglecalibration_box = QtWidgets.QGroupBox("Angular Calibration")
        self.anglecalibration_box.setLayout(QtWidgets.QHBoxLayout())
        self.anglecalibration_box.setMaximumHeight(100)
        self.calibration_info_label = QtWidgets.QLabel("Delay in s")
        self.calibration_info_label.setMaximumWidth(100)

        self.calibration_wait_time = QtWidgets.QSpinBox()
        self.calibration_wait_time.setMaximumWidth(50)

        self.calibrateButton = QtWidgets.QPushButton(self.tab_measure)
        self.calibrateButton.setText("Calibrate")
        self.calibrateButton.setObjectName("calibrateButton")
        self.calibrateButton.clicked.connect(self.trigger_calibration)
        self.anglecalibration_box.layout().addWidget(self.calibration_info_label)
        self.anglecalibration_box.layout().addWidget(self.calibration_wait_time)
        self.anglecalibration_box.layout().addWidget(self.calibrateButton)

        self.tab_config.layout().addWidget(self.anglecalibration_box)


        self.output_folder_box = QtWidgets.QGroupBox("Select output folder for measured data")
        self.output_folder_box.setMaximumHeight(100)
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

        ## MEASURE TAB
        #############################

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
        self.referenceTriggerButton.clicked.connect(self.trigger_ref_measurement)

        self.measurementTriggerButton = QtWidgets.QPushButton('Single Measurement')
        self.measurementTriggerButton.setObjectName("Single Measurement")
        self.measurementTriggerButton.setFixedSize(QtCore.QSize(200, 100))
        self.measurementTriggerButton.clicked.connect(self.measurement_ref.trigger_measurement)

        self.autoTriggerButton = QtWidgets.QPushButton('Auto Measurement')
        self.autoTriggerButton.clicked.connect(self.measurement_ref.trigger_auto_measurement)

        self.autoTriggerStopButton = QtWidgets.QPushButton('Stop Auto Measurement')
        self.autoTriggerStopButton.clicked.connect(self.measurement_ref.stop_auto_measurement)

        self.startMeasurementGroupBox.layout().addStretch()
        self.startMeasurementGroupBox.layout().addWidget(self.referenceTriggerButton)
        self.startMeasurementGroupBox.layout().addWidget(self.measurementTriggerButton)
        self.startMeasurementGroupBox.layout().addWidget(self.autoTriggerButton)
        self.startMeasurementGroupBox.layout().addWidget(self.autoTriggerStopButton)
        self.startMeasurementGroupBox.layout().addStretch()
        self.tab_measure.layout().addWidget(self.startMeasurementGroupBox)



        self.point_recommender_groupbox = QtWidgets.QGroupBox('Point Recommender')
        self.point_recommender_groupbox.setLayout(QtWidgets.QHBoxLayout())
        self.point_recommender_groupbox.setEnabled(False)

        self.recommend_point_button = QtWidgets.QPushButton('Recommend Point')
        self.recommend_point_button.clicked.connect(self.trigger_point_recommendation)

        self.start_guiding_button = QtWidgets.QPushButton('Start Guidance')
        self.start_guiding_button.clicked.connect(self.trigger_guided_measurement)

        self.clear_recommended_points_button = QtWidgets.QPushButton('Clear Recommendations')
        self.clear_recommended_points_button.clicked.connect(self.clear_recommended_points)


        self.point_recommender_groupbox.layout().addStretch()
        self.point_recommender_groupbox.layout().addWidget(self.recommend_point_button)
        self.point_recommender_groupbox.layout().addWidget(self.start_guiding_button)
        self.point_recommender_groupbox.layout().addWidget(self.clear_recommended_points_button)
        self.tab_measure.layout().addWidget(self.point_recommender_groupbox)











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

        ## DATA LIST TAB
        #############################




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
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_data), _translate("MainWindow", "Data List"))

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
        #self.measurementTriggerButton.setEnabled(True)
        #self.autoTriggerButton.setEnabled(True)
        #self.autoTriggerStopButton.setEnabled(True)
        self.vispy_canvas.meas_points.add_reference_measurement_point()

    #def remove_measurement_point(self, az, el):

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

    def updateMeasurementList(self, measurement_data):
        pass


    def update_tracker_status(self, status):
        self.label_tr1 = QtWidgets.QLabel(status["tracker1"])
        self.label_tr2 = QtWidgets.QLabel(status["tracker2"])

        if status["tracker1"] == "Tracking" and status["tracker2"] == "Tracking":
            self.manualAngleBox.setEnabled(False)
        else:
            self.manualAngleBox.setEnabled(True)

    def updateCurrentAngle(self, az, el, r):
        r = r*100
        self.azimuthLabel.setText("Az: %.0f°" % az)
        self.elevationLabel.setText("El: %.0f°" % el)
        self.radiusLabel.setText("Radius: %.0fcm" % r)

    def set_offset_speaker_z(self):
        self.measurement_ref.tracker.offset_cm['speaker_z'] = self.offset_speaker_z.value()

    def set_offset_speaker_y(self):
        self.measurement_ref.tracker.offset_cm['speaker_y'] = self.offset_speaker_y.value()

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

    def trigger_calibration(self):
        interval = self.calibration_wait_time.value() * 1000
        QtCore.QTimer.singleShot(interval, self.measurement_ref.tracker.calibrate_orientation)

    def trigger_ref_measurement(self):
        interval = 0.5 * 1000
        QtCore.QTimer.singleShot(interval, self.measurement_ref.trigger_reference_measurement)

    def trigger_left_ear_calibration(self):
        if self.measurement_ref.tracker.calibrate_ear('left'):
            self.calibrate_ear_left_label.setText(f"Calibrated, {self.measurement_ref.tracker.ear_pos_l}")
        elif hasattr(self.measurement_ref.tracker, 'ear_pos_l'):
            self.calibrate_ear_left_label.setText(f"Recalibration failed, {self.measurement_ref.tracker.ear_pos_l}")

        if hasattr(self.measurement_ref.tracker, 'head_diameter'):
            if self.measurement_ref.tracker.head_diameter is not None:
                self.head_diameter_label.setText(f'Head Diameter: {self.measurement_ref.tracker.head_diameter:.3f}, {self.measurement_ref.tracker.ear_center}')

    def trigger_right_ear_calibration(self):

        if self.measurement_ref.tracker.calibrate_ear('right'):
            self.calibrate_ear_right_label.setText(f"Calibrated, {self.measurement_ref.tracker.ear_pos_r}")
        elif hasattr(self.measurement_ref.tracker, 'ear_pos_r'):
            self.calibrate_ear_right_label.setText(f"Recalibration failed, {self.measurement_ref.tracker.ear_pos_l}")

        if hasattr(self.measurement_ref.tracker, 'head_diameter'):
            if self.measurement_ref.tracker.head_diameter is not None:
                self.head_diameter_label.setText(
                    f'Head Diameter: {self.measurement_ref.tracker.head_diameter:.3f}, {self.measurement_ref.tracker.ear_center}')

    def trigger_acoustical_centre_calibration(self):
        if self.measurement_ref.tracker.calibrate_acoustical_center():
            self.calibrate_acoustical_center_label.setText(f'Calibrated, {self.measurement_ref.tracker.acoustical_center_pos}')

    def trigger_point_recommendation(self):
            az, el = self.measurement_ref.recommend_points(1)

    def trigger_guided_measurement(self):
        self.measurement_ref.start_guided_measurement()

    def clear_recommended_points(self):
        self.measurement_ref.clear_recommended_points()

    def enable_point_recommendation(self):
        self.point_recommender_groupbox.setEnabled(True)



class InstructionsDialogBox(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):

        instruction_text = \
            "1. Mount tracker T1 on listener head. The orientation and exact position are not important, as long as it stays fixed. \n\n" \
            "2. Check if tracker roles are correct by rotating tracker T2. The angles shouldn't change since only the position of tracker T2 is used. Switch tracker roles if necessary\n\n" \
            "3. Hold tracker T2 to both ears (bottom center on ear canal) and calibrate each ear. Tracker T2 orientation does not matter here, but from now on tracker T1 on the listeners has to stay fixed & stable on the head.\n\n" \
            "4. Hold tracker T2 to acoustical center of speaker and calibrate it. Tracker orientation does not matter here\n\n" \
            "5. Put tracker T2 on a planar surface (eg. on top of speaker, floor) pointing towards the same direction as frontal view of listener. Translation does not matter here\n\n" \
            "NOTE: If acoustical center is calibrated, this calibrated position stays fixed. If the speaker is moved the calibration has to be repeated."


        super(InstructionsDialogBox, self).__init__(*args, **kwargs)

        self.setModal(False)
        self.setWindowTitle("Calibration Instructions")

        self.instructionsbox = QtWidgets.QLabel()
        self.instructionsbox.setText(instruction_text)
        self.instructionsbox.setWordWrap(True)

        Btn = QtWidgets.QDialogButtonBox.Close

        self.buttonBox = QtWidgets.QDialogButtonBox(Btn)
        self.buttonBox.clicked.connect(self.close)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.instructionsbox)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)
