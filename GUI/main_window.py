# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets
from GUI.PicButton import PicButton
from GUI.vispyWidget import VispyCanvas, VispyWidget
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
from scipy.signal import resample

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
        self.label_out_exc_2 = QtWidgets.QLabel(devs['out_excitation_2'])
        self.label_out_fb = QtWidgets.QLabel(devs['out_feedback'])
        self.label_in_left = QtWidgets.QLabel(devs['in_left'])
        self.label_in_right = QtWidgets.QLabel(devs['in_right'])
        self.label_in_fb = QtWidgets.QLabel(devs['in_feedback'])

        self.device_status_widget.setLayout(QtWidgets.QFormLayout())
        self.device_status_widget.layout().addRow(QtWidgets.QLabel("Output Excitation:"), self.label_out_exc)
        self.device_status_widget.layout().addRow(QtWidgets.QLabel("Output Excitation 2:"), self.label_out_exc_2)
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
        self.tabWidget.currentChanged.connect(self.tab_changed)

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
        self.tab_data.setLayout(QtWidgets.QGridLayout())
        #self.tab_data.layout().setAlignment(QtCore.Qt.AlignCenter)
        self.tabWidget.addTab(self.tab_data, "")
        self.tab_data_index = self.tabWidget.count()-1

        self.tab_hpc = QtWidgets.QWidget()
        self.tab_hpc.setEnabled(True)
        self.tab_hpc.setLayout(QtWidgets.QVBoxLayout())
        self.tab_hpc.layout().setAlignment(QtCore.Qt.AlignCenter)
        self.tabWidget.addTab(self.tab_hpc, "")



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

        self.radiusBox = QtWidgets.QSpinBox()
        self.radiusBox.setMinimum(20)
        self.radiusBox.setMaximum(999)
        self.radiusBox.valueChanged.connect(self.manual_update_radius)

        self.manualAngleBox = QtWidgets.QGroupBox("Set angle manually")
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Azimuth °"))
        layout.addWidget(self.azimuthBox)
        layout.addWidget(QtWidgets.QLabel("Elevation °"))
        layout.addWidget(self.elevationBox)
        layout.addWidget(QtWidgets.QLabel("Radius cm"))
        layout.addWidget(self.radiusBox)

        self.manualAngleBox.setLayout(layout)
        self.tab_measure.layout().addWidget(self.manualAngleBox)




        self.measurements_main_group = QtWidgets.QGroupBox()
        self.measurements_main_group.setLayout(QtWidgets.QHBoxLayout())

        self.measurements_main_group.layout().addWidget(QtWidgets.QLabel("Session Name:"))
        self.session_name = QtWidgets.QLineEdit()
        self.measurements_main_group.layout().addWidget(self.session_name)

        self.measurements_main_group.layout().addStretch()

        self.clear_measurements_button = QtWidgets.QPushButton("Clear / Start New")
        self.clear_measurements_button.clicked.connect(self.clear_measurements)
        self.measurements_main_group.layout().addWidget(self.clear_measurements_button)

        self.tab_measure.layout().addWidget(self.measurements_main_group)



        self.startMeasurementGroupBox = QtWidgets.QGroupBox('Start Measurement')
        self.startMeasurementGroupBox.setLayout(QtWidgets.QGridLayout())

        self.referenceTriggerButton = QtWidgets.QPushButton('Reference Measurement')
        self.referenceTriggerButton.setObjectName("Reference Measurement")
        self.referenceTriggerButton.clicked.connect(self.trigger_ref_measurement)

        self.measurementTriggerButton = QtWidgets.QPushButton('Single Measurement')
        self.measurementTriggerButton.setObjectName("Single Measurement")
        self.measurementTriggerButton.setFixedSize(QtCore.QSize(200, 100))
        self.measurementTriggerButton.clicked.connect(self.measurement_ref.trigger_measurement)

        self.autoTriggerButton = QtWidgets.QPushButton('Auto Measurement')
        self.autoTriggerButton.clicked.connect(self.measurement_ref.trigger_auto_measurement)

        self.autoMeasurementTriggerProgress = QtWidgets.QProgressBar()
        self.autoMeasurementTriggerProgress.setVisible(False)

        self.autoTriggerStopButton = QtWidgets.QPushButton('Stop Auto Measurement')
        self.autoTriggerStopButton.clicked.connect(self.measurement_ref.stop_auto_measurement)

        #self.startMeasurementGroupBox.layout().addStretch()
        self.startMeasurementGroupBox.layout().addWidget(self.referenceTriggerButton, 1, 0, 1, 1)
        self.startMeasurementGroupBox.layout().addWidget(self.measurementTriggerButton, 0, 1, 3, 1)
        self.startMeasurementGroupBox.layout().addWidget(self.autoTriggerButton, 1, 2, 1, 1)
        self.startMeasurementGroupBox.layout().addWidget(self.autoMeasurementTriggerProgress, 2, 2, 1, 1)
        self.startMeasurementGroupBox.layout().addWidget(self.autoTriggerStopButton, 1, 3, 1, 1)
        #self.startMeasurementGroupBox.layout().addStretch()
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

        self.plot_widget = PlotWidget()

        self.plotgroupbox.layout().addWidget(self.plot_widget)
        self.tab_measure.layout().addWidget(self.plotgroupbox)

        ## DATA LIST TAB
        #############################
        self.positions_table = QtWidgets.QTableView()
        self.positions_table.setModel(self.measurement_ref.positions_table_model)
        self.positions_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.positions_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.positions_table.verticalHeader().show()
        self.positions_table.horizontalHeader().setSectionResizeMode(1)
        self.positions_table.verticalHeader().setSectionResizeMode(3)
        self.positions_table.setFont(QtGui.QFont('Helvetica', 13))
        self.positions_table.setShowGrid(False)
        #self.positions_table.setMaximumWidth(300)



        self.positions_table_selection = self.positions_table.selectionModel()
        self.positions_table_selection.currentRowChanged.connect(self.data_table_selection)

        self.tab_data.layout().addWidget(self.positions_table, 0, 0, 1, 1)

        self.remove_measurement_button = QtWidgets.QPushButton("Delete Selected")
        self.remove_measurement_button.clicked.connect(self.remove_measurement)
        self.tab_data.layout().addWidget(self.remove_measurement_button, 1, 0, 1, 1)

        self.plot_widget2 = PlotWidget()
        #self.plot_widget2.setMaximumWidth(200)
        self.tab_data.layout().addWidget(self.plot_widget2, 0, 1, 1, 1)


        ## HEADPHONE COMPENSATION TAB
        #############################

        self.hp_main_group = QtWidgets.QGroupBox()
        self.hp_main_group.setLayout(QtWidgets.QHBoxLayout())

        self.hp_main_group.layout().addWidget(QtWidgets.QLabel("Headphone Name:"))
        self.headphone_name = QtWidgets.QLineEdit()
        self.hp_main_group.layout().addWidget(self.headphone_name)

        self.hp_main_group.layout().addStretch()

        self.clear_hp_measurements_button = QtWidgets.QPushButton("Clear / Start New")
        self.clear_hp_measurements_button.clicked.connect(self.clear_hp_measurements)
        self.hp_main_group.layout().addWidget(self.clear_hp_measurements_button)

        self.tab_hpc.layout().addWidget(self.hp_main_group)

        self.hp_controls_group = QtWidgets.QGroupBox()
        self.hp_controls_group.setLayout(QtWidgets.QHBoxLayout())

        self.hp_measurement_count = QtWidgets.QLabel("")
        self.hp_measurement_count.setFixedWidth(16)
        self.hp_controls_group.layout().addWidget(self.hp_measurement_count)

        self.trigger_hp_measurement_button = QtWidgets.QPushButton("Trigger Headphone  \n Measurement")
        self.trigger_hp_measurement_button.clicked.connect(self.trigger_hp_measurement)
        self.trigger_hp_measurement_button.setFixedSize(QtCore.QSize(200, 100))
        self.hp_controls_group.layout().addWidget(self.trigger_hp_measurement_button)

        self.remove_hp_measurement_button = QtWidgets.QPushButton("Remove Last \n HP Measurement")
        self.remove_hp_measurement_button.clicked.connect(self.remove_hp_measurement)
        self.remove_measurement_button.setFixedSize(QtCore.QSize(200, 50))
        self.hp_controls_group.layout().addWidget(self.remove_hp_measurement_button)

        self.hp_controls_group.layout().addStretch()
        self.hp_controls_group.layout().addWidget(QtWidgets.QLabel("Reg Beta:"))

        self.regularization_beta_box = QtWidgets.QDoubleSpinBox()
        self.regularization_beta_box.setMaximum(1.0)
        self.regularization_beta_box.setSingleStep(0.05)
        self.regularization_beta_box.setValue(0.4)
        self.regularization_beta_box.setFixedWidth(100)
        self.regularization_beta_box.valueChanged.connect(self.set_regularization_beta)
        self.hp_controls_group.layout().addWidget(self.regularization_beta_box)

        self.tab_hpc.layout().addWidget(self.hp_controls_group)
        #self.plot_hpc_widget = PlotWidget()
        #self.tab_hpc.layout().addWidget(self.plot_hpc_widget)


        self.plot_hpirs = Figure()
        self.plot_hpirs.set_facecolor("none")
        self.plot_hpirs_canvas = FigureCanvas(self.plot_hpirs)
        self.plot_hpirs_canvas.setStyleSheet("background-color:transparent;")
        self.tab_hpc.layout().addWidget(self.plot_hpirs_canvas)



        self.plot_hpc = Figure()
        self.plot_hpc.set_facecolor('none')
        self.plot_hpc_canvas = FigureCanvas(self.plot_hpc)
        self.plot_hpc_canvas.setStyleSheet("background-color:transparent;")
        self.tab_hpc.layout().addWidget(self.plot_hpc_canvas)

        self.plot_hptf(np.array([]))
        self.plot_hpc_estimate(np.array([]), np.array([]))


        ## Layout finalilzation

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
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_hpc), _translate("MainWindow", "Headphone Compensation"))


        self.positions_table.setColumnWidth(0, self.positions_table.width() / 3)
        self.positions_table.setColumnWidth(1, self.positions_table.width() / 3)
        self.positions_table.setColumnWidth(2, self.positions_table.width() / 3)

        print("Width: " + str(self.positions_table.width()))


    def manual_update_az(self):
        self.measurement_ref.tracker.fallback_angle[0] = self.azimuthBox.value()

    def manual_update_el(self):
        self.measurement_ref.tracker.fallback_angle[1] = self.elevationBox.value()
    def manual_update_radius(self):
        self.measurement_ref.tracker.fallback_angle[2] = self.radiusBox.value() / 100

    def add_measurement_point(self, az, el):
        self.vispy_canvas.meas_points.add_point(az, el)

    def add_reference_point(self):
        #self.measurementTriggerButton.setEnabled(True)
        #self.autoTriggerButton.setEnabled(True)
        #self.autoTriggerStopButton.setEnabled(True)
        self.vispy_canvas.ref_points.add_point(0, 0)

    #def remove_measurement_point(self, az, el):

    def plot_recordings(self, rec_l, rec_r, fb_loop):
        self.plot_widget.plot_recordings(rec_l, rec_r, fb_loop)

    def plot_IRs(self, ir_l, ir_r):
        self.plot_widget.plot_IRs(ir_l, ir_r)

    def updateMeasurementList(self, measurement_data):
        pass


    def update_tracker_status(self, status):
        self.label_tr1 = QtWidgets.QLabel(status["tracker1"])
        self.label_tr2 = QtWidgets.QLabel(status["tracker2"])

        if status["tracker1"] == "Tracking" and status["tracker2"] == "Tracking":
            self.manualAngleBox.setVisible(False)
        else:
            self.manualAngleBox.setVisible(True)

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

    def data_table_selection(self, selected, deselected):
        self.vispy_canvas.meas_points.deselect_points(deselected.row())
        self.vispy_canvas.meas_points.select_point(selected.row())

        print("Data Table Selection: " + str(selected.row()))
        idx = selected.row()
        try:
            ir_l = self.measurement_ref.measurements[idx, 0, :]
            ir_r = self.measurement_ref.measurements[idx, 1, :]
            raw_l = self.measurement_ref.raw_signals[idx, 0, :]
            raw_r = self.measurement_ref.raw_signals[idx, 1, :]
            fb = self.measurement_ref.raw_feedbackloop[idx, 0, :]

            self.plot_widget2.plot_IRs(ir_l, ir_r, plot='spectrogram')
            self.plot_widget2.plot_recordings(raw_l, raw_r, fb, plot='spectrogram')

        except IndexError:
            print("Could not plot data: Invalid id")


    def tab_changed(self, index):
        try:
            if index is not self.tab_data_index:
                self.vispy_canvas.meas_points.deselect_points()
            else:
                numRows = self.positions_table.model().rowCount(QtCore.QModelIndex())
                self.positions_table.selectRow(numRows-1)

        except:
            pass

    def clear_measurements(self):
        self.measurement_ref.delete_all_measurements()

    def remove_measurement(self):
        indexes = self.positions_table_selection.selectedRows()
        for index in indexes:
            id = index.row()
            dialog = QtWidgets.QMessageBox
            ret = dialog.question(self.myMainWindow,'', "Are you sure you want to delete this measurement?", dialog.Yes | dialog.No)

            if ret == dialog.Yes:
                print("Deleting Measurement " + str(id))
                self.measurement_ref.delete_measurement(id)

    def update_dev_status(self):
        devs = self.measurement_ref.devices

        self.label_out_exc.setText(devs['out_excitation'])
        self.label_out_exc_2.setText(devs['out_excitation_2'])
        self.label_out_fb.setText(devs['out_feedback'])
        self.label_in_left.setText(devs['in_left'])
        self.label_in_right.setText(devs['in_right'])
        self.label_in_fb.setText(devs['in_feedback'])

    def trigger_hp_measurement(self):
        self.measurement_ref.hp_measurement()

    def remove_hp_measurement(self):
        self.measurement_ref.remove_hp_measurement()

    # def plot_hpc_recordings(self, rec_l, rec_r, fb_loop):
    #    self.plot_hpc_widget.plot_recordings(rec_l, rec_r, fb_loop)

    def plot_hptf(self, hpc_irs, hpc_average=None, fs=48000):

        try:
            M = np.size(hpc_irs, 0)
            N = np.size(hpc_irs, 2)
        except IndexError:
            M = 0
            N = 0

        plot_resolution = 1025
        nyquist = int(N / 2 + 1)

        f_vals = np.linspace(0, fs/2, plot_resolution)

        matplotlib.rcParams.update({'font.size': 5})

        self.plot_hpirs.clf()

        ax1 = self.plot_hpirs.add_subplot(211)
        ax1.clear()
        ax1.set_title("Headphone IR L")
        ax1.set_xscale('log')
        #ax1.set_ylim(-12, 12)
        ax1.set_xlim(20, 20000)
        ax1.set_xticks([20, 100, 1000, 10000, 20000])

        ax2 = self.plot_hpirs.add_subplot(212)
        ax2.clear()
        ax2.set_title("Headphone IR R")
        ax2.set_xscale('log')
        ax2.set_xlim(20, 20000)
        ax2.set_xticks([20, 100, 1000, 10000, 20000])

        for i in range(M):
            ir = hpc_irs[i, 0, :]
            magFilter = np.abs(np.fft.fft(ir))
            magFilter = magFilter[:nyquist]
            magFilter = 20 * np.log10(abs(magFilter))
            magFilter = resample(magFilter, plot_resolution)
            ax1.plot(f_vals, magFilter, linewidth=0.5)

            ir = hpc_irs[i, 1, :]
            magFilter = np.abs(np.fft.fft(ir))
            magFilter = magFilter[:nyquist]
            magFilter = 20 * np.log10(abs(magFilter))
            magFilter = resample(magFilter, plot_resolution)
            ax2.plot(f_vals, magFilter, linewidth=0.5)

        y_low1, y_high1 = ax1.get_ylim()
        y_low2, y_high2 = ax2.get_ylim()
        y_low = min(y_low1, y_low2)
        y_high = min(y_high1, y_high2)
        ax1.set_ylim(y_low, y_high)
        ax2.set_ylim(y_low, y_high)

        # ax2 = self.plot_hpc.add_subplot(212)
        # ax2.clear()
        # ax2.set_title("Headphone IR R")
        # ax2.set_xscale('log')
        #
        # for hpc in hpc_list['r']:
        #     #ax2.plot(hpc)
        #     ax2.magnitude_spectrum(hpc, Fs=fs, scale='dB')


        self.plot_hpirs_canvas.draw()

    def plot_hpc_estimate(self, H_l, H_r, fs=48000):

        matplotlib.rcParams.update({'font.size': 5})

        ax = self.plot_hpc.gca()

        ax.clear()
        ax.set_title("Headphone Compensation (Preview)")
        ax.set_xscale('log')
        ax.set_xlim(20, 20000)
        ax.set_ylim(-30, 10)
        ax.set_xticks([20, 100, 1000, 10000, 20000])

        nq = int(np.size(H_l) / 2 + 1)
        f_vals = np.linspace(0, 24000, nq)

        try:
            magFilter_l = H_l
            magFilter_l = magFilter_l[:nq]
            magFilter_l = 20 * np.log10(abs(magFilter_l))
            l, = ax.plot(f_vals, magFilter_l, linewidth=2)
            l.set_label("Left Ear")

            magFilter_r = H_r
            magFilter_r = magFilter_r[:nq]
            magFilter_r = 20 * np.log10(abs(magFilter_r))
            r, = ax.plot(f_vals, magFilter_r, linewidth=2)
            r.set_label("Right Ear")

            ax.legend()

        except ValueError:
            pass


        # # set y limits according to displayed values
        # low, high = ax.get_xlim()
        # plotted_bin_ids = np.where((f_vals > low) & (f_vals < high))
        #
        # low_y = np.array([magFilter_l[plotted_bin_ids], magFilter_l[plotted_bin_ids]]).min()
        # high_y = np.array([magFilter_r[plotted_bin_ids], magFilter_r[plotted_bin_ids]]).max()
        #
        # ax.set_ylim((low_y+5) + (5-np.mod((a+5), 5)), high_y)

        self.plot_hpc_canvas.draw()

    def set_regularization_beta(self):
        self.measurement_ref.estimate_hpcf(self.regularization_beta_box.value())

    def clear_hp_measurements(self):
        self.measurement_ref.remove_all_hp_measurements()
        self.session_name.clear()


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

class PlotWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

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
        self.plot1.set_facecolor("none")
        self.plot1_canvas = FigureCanvas(self.plot1)
        self.plot1_canvas.setStyleSheet("background-color:transparent;")
        self.tab_rec.layout().addWidget(self.plot1_canvas)

        self.plot2 = Figure()
        self.plot2.set_facecolor("none")
        self.plot2_canvas = FigureCanvas(self.plot2)
        self.plot2_canvas.setStyleSheet("background-color:transparent;")
        self.tab_ir.layout().addWidget(self.plot2_canvas)

        self.layout().addWidget(self.plot_tab_widget)

        self.plot_tab_widget.setTabText(0, "REC")
        self.plot_tab_widget.setTabText(1, "IR")

        self.spec_nfft = 512

        self.spec_noverlap = 300

    def plot_recordings(self, rec_l, rec_r, fb_loop, fs=48000, plot='waveform'):
        matplotlib.rcParams.update({'font.size': 5})

        self.plot1.clf()

        ax1 = self.plot1.add_subplot(311)
        ax1.clear()
        if plot == 'waveform':
            ax1.plot(rec_l)
        elif plot == 'spectrogram':
            _,_,_, cax  = ax1.specgram(rec_l, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
            self.plot1.colorbar(cax)

        ax2 = self.plot1.add_subplot(312)
        ax2.clear()
        if plot == 'waveform':
            ax2.plot(rec_r)
        elif plot == 'spectrogram':
            _,_,_, cax2  = ax2.specgram(rec_r, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
            self.plot1.colorbar(cax2)

        ax3 = self.plot1.add_subplot(313)
        ax3.clear()
        if plot == 'waveform':
            ax3.plot(fb_loop)
        elif plot == 'spectrogram':
            _,_,_, cax3  = ax3.specgram(fb_loop, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
            self.plot1.colorbar(cax3)

        self.plot1_canvas.draw()

    def plot_IRs(self, ir_l, ir_r, fs=48000, plot='waveform'):
        matplotlib.rcParams.update({'font.size': 5})

        self.plot2.clf()

        ax1 = self.plot2.add_subplot(211)
        ax1.clear()

        if plot=='waveform':
            ax1.plot(ir_l)
        elif plot=='spectrogram':
            _,_,_, cax = ax1.specgram(ir_l, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
            self.plot2.colorbar(cax).set_label('dB')

        ax2 = self.plot2.add_subplot(212)
        ax2.clear()

        if plot=='waveform':
            ax2.plot(ir_r)
        elif plot=='spectrogram':
            _,_,_, cax2 = ax2.specgram(ir_r, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
            self.plot2.colorbar(cax2).set_label('dB')

        self.plot2_canvas.draw()

