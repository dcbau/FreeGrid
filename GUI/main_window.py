# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets
from GUI.vispyWidget import VispyCanvas
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
from scipy.signal import resample
import os
from GUI.audio_device_widget import AudioDeviceWidget


reproduction_available = False


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
        # devs = self.measurement_ref.devices
        #
        # self.label_out_exc = QtWidgets.QLabel(devs['out_excitation'])
        # self.label_out_exc_2 = QtWidgets.QLabel(devs['out_excitation_2'])
        # self.label_out_fb = QtWidgets.QLabel(devs['out_feedback'])
        # self.label_in_left = QtWidgets.QLabel(devs['in_left'])
        # self.label_in_right = QtWidgets.QLabel(devs['in_right'])
        # self.label_in_fb = QtWidgets.QLabel(devs['in_feedback'])
        #
        self.device_status_widget.setLayout(QtWidgets.QHBoxLayout())
        # self.device_status_widget.layout().addRow(QtWidgets.QLabel("Output Excitation:"), self.label_out_exc)
        # self.device_status_widget.layout().addRow(QtWidgets.QLabel("Output Excitation 2:"), self.label_out_exc_2)
        # self.device_status_widget.layout().addRow(QtWidgets.QLabel("Output Feedback Loop:"), self.label_out_fb)
        # self.device_status_widget.layout().addRow(QtWidgets.QLabel("Input Left Ear Mic:"), self.label_in_left)
        # self.device_status_widget.layout().addRow(QtWidgets.QLabel("Input Right Ear Mic:"), self.label_in_right)
        # self.device_status_widget.layout().addRow(QtWidgets.QLabel("Input Feedback Loop:"), self.label_in_fb)

        #self.device_status_widget.layout().setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        #self.device_status_widget.setMaximumHeight(200)
        self.device_status_widget.layout().addWidget(AudioDeviceWidget())


        # TRACKER STATUS WIDGET

        self.tracker_status_widget = QtWidgets.QGroupBox("Vive Tracker Status")
        tracker_status = self.measurement_ref.tracker.check_tracker_availability()

        self.tracker1_status_label = QtWidgets.QLabel(tracker_status["tracker1"])
        self.tracker2_status_label = QtWidgets.QLabel(tracker_status["tracker2"])

        self.tracker1_label = QtWidgets.QLabel("(Head) Tracker 1:")
        self.tracker2_label = QtWidgets.QLabel("Tracker 2:")

        self.tracker_status_widget.setLayout(QtWidgets.QFormLayout())
        self.tracker_status_widget.layout().addRow(self.tracker1_label, self.tracker1_status_label)
        self.tracker_status_widget.layout().addRow(self.tracker2_label, self.tracker2_status_label)

        self.tracker_status_widget.setMaximumHeight(100)

        # OSC STATUS WIDGET

        self.osc_status_box = QtWidgets.QGroupBox("OSC Input Status")
        self.osc_status_box.setMaximumHeight(100)
        self.osc_status_box.setLayout(QtWidgets.QVBoxLayout())

        self.osc_status_indicator = QtWidgets.QCheckBox(" OSC Input")
        self.osc_status_indicator.setStyleSheet("QCheckBox::indicator"
                                                "{"
                                                "background-color : lightgrey;"
                                                "}")
        self.osc_status_indicator.setCheckable(False)
        self.osc_status_box.layout().addWidget(self.osc_status_indicator)

        self.osc_status_box.hide()








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
        self.tab_config.layout().setAlignment(QtCore.Qt.AlignTop)
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

        self.tab_reproduction = QtWidgets.QWidget()
        self.tab_reproduction.setEnabled(True)
        self.tab_reproduction.setLayout(QtWidgets.QVBoxLayout())
        self.tab_reproduction.layout().setAlignment(QtCore.Qt.AlignTop)

        if reproduction_available:
            self.tabWidget.addTab(self.tab_reproduction, "Reproduction")
            self.tab_reproduction_index = self.tabWidget.count()-1

        # Config Tab
        #############################
        #############################

        # Config Tab
        #   Select Tracking Input
        ############################

        self.tracking_input_box = QtWidgets.QGroupBox("Tracking Input")
        self.tracking_input_box.setFixedHeight(70)
        self.tracking_input_box.setLayout(QtWidgets.QHBoxLayout())

        self.tracking_input_vive = QtWidgets.QRadioButton("Vive Trackers")
        self.tracking_input_vive.setChecked(True)
        self.tracking_input_vive.sourcename = "Vive"
        self.tracking_input_vive.toggled.connect(self.select_tracking_input)
        self.tracking_input_box.layout().addWidget(self.tracking_input_vive)

        self.tracking_input_OSC_direct = QtWidgets.QRadioButton("External: OSC (Az|El|R)")
        self.tracking_input_OSC_direct.sourcename = "OSC_direct"
        self.tracking_input_OSC_direct.toggled.connect(self.select_tracking_input)
        self.tracking_input_box.layout().addWidget(self.tracking_input_OSC_direct)

        #radiobutton = QtWidgets.QRadioButton("External: Vive OSC (Raw Data)")
        #radiobutton.sourcename = "OSC_vive"
        #radiobutton.toggled.connect(self.select_tracking_input)
        #self.tracking_input_box.layout().addWidget(radiobutton)

        self.tab_config.layout().addWidget(self.tracking_input_box)

        # Config Tab
        # Vive Tracker Box
        #   Show Instructions Dialog Box:
        ###########################


        self.vivetracker_box = QtWidgets.QGroupBox("Tracker Calibration")
        self.vivetracker_box.setLayout(QtWidgets.QVBoxLayout())
        self.vivetracker_box.layout().setAlignment(QtCore.Qt.AlignTop)
        self.vivetracker_box.setFixedHeight(500)

        self.tab_config.layout().addWidget(self.vivetracker_box)

        self.dlg = InstructionsDialogBox()
        self.show_instructions_button = QtWidgets.QPushButton()
        self.show_instructions_button.setText("Show Calibration Instructions")
        self.show_instructions_button.clicked.connect(self.dlg.show)
        self.show_instructions_button.setMaximumWidth(200)
        self.vivetracker_box.layout().addWidget(self.show_instructions_button)


        # Config Tab
        # Vive Tracker Box
        #   Switch Trackers Box:
        ###########################

        self.switchTrackersButton = QtWidgets.QPushButton()
        self.switchTrackersButton.setText("Switch Tracker Roles")
        self.switchTrackersButton.setObjectName("switchTrackersButton")
        self.switchTrackersButton.setMaximumWidth(200)
        self.switchTrackersButton.clicked.connect(self.switch_trackers)
        self.vivetracker_box.layout().addWidget(self.switchTrackersButton)

        # Config Tab
        # Vive Tracker Box
        #   Delay trackers textfield:
        ###########################

        self.delay_calibration_layout = QtWidgets.QHBoxLayout()
        self.delay_calibration_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.vivetracker_box.layout().addLayout(self.delay_calibration_layout)
        self.calibration_info_label = QtWidgets.QLabel("Delay calibration triggers (s)")
        self.delay_calibration_layout.addWidget(self.calibration_info_label)
        self.calibration_wait_time = QtWidgets.QSpinBox()
        self.delay_calibration_layout.addWidget(self.calibration_wait_time)

        # Config Tab
        # Vive Tracker Box
        #   Head Dimensions Dialog:
        ###########################

        self.head_dimensions_dialog = QtWidgets.QDialog()

        self.head_dimensions_dialog.setModal(False)
        self.head_dimensions_dialog.setWindowTitle("Measure Head Dimensions")

        Btn = QtWidgets.QDialogButtonBox.Close
        self.head_dimensions_dialog.buttonBox = QtWidgets.QDialogButtonBox(Btn)
        self.head_dimensions_dialog.buttonBox.clicked.connect(self.head_dimensions_dialog.close)

        self.head_dimensions_dialog.setLayout(QtWidgets.QVBoxLayout())
        self.head_dimensions_dialog.layout().setAlignment(QtCore.Qt.AlignLeft)

        self.head_dimensions_info = QtWidgets.QLabel("Measure the width and length of the head by holding the tracker to the left, right, front and back of the head (above the ears). This data is not mandatory for the measurement, but can be used as meta data during post processing. It is stored along with the HRIR data.")
        self.head_dimensions_info.setWordWrap(True)
        self.head_dimensions_dialog.layout().addWidget(self.head_dimensions_info)

        self.head_dimensions_formlayout = QtWidgets.QFormLayout()
        self.head_dimensions_dialog.layout().addLayout(self.head_dimensions_formlayout)

        calibration_button_width = 180
        calibration_button_size = QtCore.QSize(calibration_button_width, 50)

        self.calibrate_left_head = QtWidgets.QPushButton(text='Left Side')
        self.calibrate_left_head.setAutoDefault(False)
        # self.calibrate_ear_left.setFixedSize(calibration_button_size)
        self.calibrate_left_head.setFixedWidth(calibration_button_width)
        self.calibrate_left_head.clicked.connect(lambda: self.calibrate(self.calibrate_head_left))
        self.calibrate_left_head_label = QtWidgets.QLabel(text="Uncalibrated")
        self.head_dimensions_formlayout.addRow(self.calibrate_left_head, self.calibrate_left_head_label)

        self.calibrate_right_head = QtWidgets.QPushButton(text='Right Side')
        self.calibrate_right_head.setAutoDefault(False)

        # self.calibrate_ear_right.setFixedSize(calibration_button_size)
        self.calibrate_right_head.setFixedWidth(calibration_button_width)
        self.calibrate_right_head.clicked.connect(lambda: self.calibrate(self.calibrate_head_right))
        self.calibrate_right_head_label = QtWidgets.QLabel(text="Uncalibrated")
        self.head_dimensions_formlayout.addRow(self.calibrate_right_head, self.calibrate_right_head_label)

        self.head_width_label = QtWidgets.QLabel(text="Head Width: - ")
        self.head_dimensions_formlayout.addRow(QtWidgets.QLabel(""), self.head_width_label)

        self.calibrate_front_head = QtWidgets.QPushButton(text='Front Of Head')
        self.calibrate_front_head.setAutoDefault(False)
        # self.calibrate_front_head.setFixedSize(calibration_button_size)
        self.calibrate_front_head.setFixedWidth(calibration_button_width)
        self.calibrate_front_head.clicked.connect(lambda: self.calibrate(self.calibrate_head_front))
        self.calibrate_front_head_label = QtWidgets.QLabel(text="Uncalibrated")
        self.head_dimensions_formlayout.addRow(self.calibrate_front_head, self.calibrate_front_head_label)

        self.calibrate_back_head = QtWidgets.QPushButton(text='Back Of Head')
        self.calibrate_back_head.setAutoDefault(False)
        # self.calibrate_back_head.setFixedSize(calibration_button_size)
        self.calibrate_back_head.setFixedWidth(calibration_button_width)
        self.calibrate_back_head.clicked.connect(lambda: self.calibrate(self.calibrate_head_back))
        self.calibrate_back_head_label = QtWidgets.QLabel(text="Uncalibrated")
        self.head_dimensions_formlayout.addRow(self.calibrate_back_head, self.calibrate_back_head_label)

        self.head_length_label = QtWidgets.QLabel(text="Head Length: - ")
        self.head_dimensions_formlayout.addRow(QtWidgets.QLabel(""), self.head_length_label)

        self.head_dimensions_dialog.layout().addWidget(self.head_dimensions_dialog.buttonBox)


        self.show_head_dimensions = QtWidgets.QPushButton()
        self.show_head_dimensions.setText("Optional: Head Dimensions")
        self.show_head_dimensions.clicked.connect(self.head_dimensions_dialog.show)
        self.show_head_dimensions.setMaximumWidth(200)
        self.vivetracker_box.layout().addWidget(self.show_head_dimensions)

        # Config Tab
        # Vive Tracker Box
        #    Calibration Box

        self.calibration_box = QtWidgets.QGroupBox("Tracker Calibration")
        self.calibration_box.setLayout(QtWidgets.QVBoxLayout())
        self.calibration_box.layout().setAlignment(QtCore.Qt.AlignLeft)
        self.vivetracker_box.layout().addWidget(self.calibration_box)

        self.calibrations_formlayout = QtWidgets.QFormLayout()
        self.calibration_box.layout().addLayout(self.calibrations_formlayout)


        calibration_button_width = 180
        calibration_button_size = QtCore.QSize(calibration_button_width, 50)


        self.calibrate_ear_left = QtWidgets.QPushButton(text='Calibrate Left Ear')
        #self.calibrate_ear_left.setFixedSize(calibration_button_size)
        self.calibrate_ear_left.setFixedWidth(calibration_button_width)
        self.calibrate_ear_left.clicked.connect(lambda: self.calibrate(self.calibrate_left_ear))
        self.calibrate_ear_left_label = QtWidgets.QLabel(text="Uncalibrated")
        self.calibrations_formlayout.addRow(self.calibrate_ear_left, self.calibrate_ear_left_label)

        self.calibrate_ear_right = QtWidgets.QPushButton(text='Calibrate Right Ear')
        #self.calibrate_ear_right.setFixedSize(calibration_button_size)
        self.calibrate_ear_right.setFixedWidth(calibration_button_width)
        self.calibrate_ear_right.clicked.connect(lambda: self.calibrate(self.calibrate_right_ear))
        self.calibrate_ear_right_label = QtWidgets.QLabel(text="Uncalibrated")
        self.calibrations_formlayout.addRow(self.calibrate_ear_right, self.calibrate_ear_right_label)

        self.calibrate_acoustical_center = QtWidgets.QPushButton(text='Calibrate Speaker')
        #self.calibrate_acoustical_center.setFixedSize(calibration_button_size)
        self.calibrate_acoustical_center.setFixedWidth(calibration_button_width)
        self.calibrate_acoustical_center.clicked.connect(lambda: self.calibrate(self.calibrate_acoustical_centre))
        self.calibrate_acoustical_center_label = QtWidgets.QLabel(text="Uncalibrated")
        self.calibrations_formlayout.addRow(self.calibrate_acoustical_center, self.calibrate_acoustical_center_label)



        self.calibrateButton = QtWidgets.QPushButton(self.tab_measure)
        self.calibrateButton.setText("Calibrate Orientation")
        self.calibrateButton.setObjectName("calibrateButton")
        #self.calibrateButton.setFixedSize(calibration_button_size)
        self.calibrateButton.setFixedWidth(calibration_button_width)
        self.calibrateButton.clicked.connect(lambda: self.calibrate(self.calibrate_orientation))
        self.calibrate_orientation_label = QtWidgets.QLabel("Uncalibrated")

        self.calibrations_formlayout.addRow(self.calibrateButton, self.calibrate_orientation_label)


        # Config Tab
        #   OSC Config Box
        ############################

        self.osc_config_box = QtWidgets.QGroupBox("OSC Configuration")
        self.osc_config_box.setLayout(QtWidgets.QVBoxLayout())
        self.osc_config_box.setFixedHeight(500)
        self.osc_config_box.layout().setAlignment(QtCore.Qt.AlignTop)
        self.osc_config_box.hide()

        self.osc_ip_label = QtWidgets.QLabel("Current Host IP: ")
        self.osc_port_label = QtWidgets.QLabel("OSC Server Port: ")
        self.osc_address_label = QtWidgets.QLabel("Listening for list of [Az, El, R] on osc-address '/guided_hrtfs/angle'")
        self.osc_address_label.setWordWrap(True)

        self.osc_config_box.layout().addWidget(self.osc_ip_label)
        self.osc_config_box.layout().addWidget(self.osc_port_label)
        self.osc_config_box.layout().addWidget(self.osc_address_label)


        self.tab_config.layout().addWidget(self.osc_config_box)

        # Config Tab
        #   Measurement Parameters Box:
        ############################

        self.measuremet_paramteres_box = QtWidgets.QGroupBox("Measurement Parameters")
        self.measuremet_paramteres_box.setLayout(QtWidgets.QVBoxLayout())


        self.sweep_parameters_dialog = QtWidgets.QDialog()
        self.sweep_parameters_dialog.setModal(False)
        self.sweep_parameters_dialog.setWindowTitle("Sweep Parameters")

        Btn_ok = QtWidgets.QDialogButtonBox.Ok
        self.sweep_parameters_dialog.buttonBox = QtWidgets.QDialogButtonBox(Btn_ok)
        self.sweep_parameters_dialog.buttonBox.clicked.connect(self.update_sweep_parameters)

        self.sweep_parameters_dialog.setLayout(QtWidgets.QVBoxLayout())
        self.sweep_parameters_dialog.layout().setAlignment(QtCore.Qt.AlignLeft)

        self.sweep_parameters_formlayout = QtWidgets.QFormLayout()
        self.sweep_parameters_dialog.layout().addLayout(self.sweep_parameters_formlayout)

        # get current parameters
        sweep_params = self.measurement_ref.measurement.get_sweep_parameters()

        # add row entries for each parameter
        self.sweeplength_sec = QtWidgets.QLineEdit(str(sweep_params['sweeplength_sec']))
        self.sweep_parameters_formlayout.addRow(self.sweeplength_sec, QtWidgets.QLabel(text='Sweep length (sec)'))

        self.post_silence_sec = QtWidgets.QLineEdit(str(sweep_params['post_silence_sec']))
        self.sweep_parameters_formlayout.addRow(self.post_silence_sec, QtWidgets.QLabel(text='Silence after sweep (sec)'))

        self.f_start = QtWidgets.QLineEdit(str(sweep_params['f_start']))
        self.sweep_parameters_formlayout.addRow(self.f_start, QtWidgets.QLabel(text='Sweep start frequency (Hz)'))

        self.f_end = QtWidgets.QLineEdit(str(sweep_params['f_end']))
        self.sweep_parameters_formlayout.addRow(self.f_end, QtWidgets.QLabel(text='Sweep stop frequency (Hz)'))

        self.amp_db = QtWidgets.QLineEdit(str(sweep_params['amp_db']))
        self.sweep_parameters_formlayout.addRow(self.amp_db, QtWidgets.QLabel(text='Sweep gain (dB)'))

        self.fade_out_samples = QtWidgets.QLineEdit(str(sweep_params['fade_out_samples']))
        self.sweep_parameters_formlayout.addRow(self.fade_out_samples, QtWidgets.QLabel(text='Fadeout before sweep end (samples)'))

        self.sweep_parameters_errormessage = QtWidgets.QLabel("Invalid Sweep Paramters")
        self.sweep_parameters_formlayout.addRow(self.sweep_parameters_errormessage)
        self.sweep_parameters_errormessage.setVisible(False)

        # add bottom button box
        self.sweep_parameters_dialog.layout().addWidget(self.sweep_parameters_dialog.buttonBox)

        self.show_sweep_parameters = QtWidgets.QPushButton()
        self.show_sweep_parameters.setText("Set Sweep Parameters")
        self.show_sweep_parameters.clicked.connect(self.sweep_parameters_dialog.show)
        self.show_sweep_parameters.setMaximumWidth(200)
        self.measuremet_paramteres_box.layout().addWidget(self.show_sweep_parameters)

        self.tab_config.layout().addWidget(self.measuremet_paramteres_box)


        # Config Tab
        #   Output Folder Box:
        ############################

        self.output_folder_box = QtWidgets.QGroupBox("Select output folder for measured data")
        self.output_folder_box.setFixedHeight(80)
        self.output_folder_box.setLayout(QtWidgets.QHBoxLayout())
        path = os.getcwd()
        path = os.path.join(path, "Measurements")
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except:
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

        # Config Tab
        #   Send OSC Box:
        ############################
        self.send_osc_box = QtWidgets.QGroupBox("Send OSC data to external application")
        self.send_osc_box.setFixedHeight(200)
        self.send_osc_box.setLayout(QtWidgets.QFormLayout())
        self.send_osc_box.layout().setLabelAlignment(QtCore.Qt.AlignLeft)


        ip, port, address = self.measurement_ref.get_osc_parameters()

        self.send_osc_ip_select = QtWidgets.QLineEdit()
        self.send_osc_ip_select.setText(ip)
        self.send_osc_box.layout().addRow("OSC IP Address: ", self.send_osc_ip_select)

        self.send_osc_port_select = QtWidgets.QLineEdit()
        self.send_osc_port_select.setText(f'{port}')
        self.send_osc_box.layout().addRow("OSC Port: ", self.send_osc_port_select)

        self.send_osc_address_select = QtWidgets.QLineEdit()
        self.send_osc_address_select.setText(address)
        self.send_osc_box.layout().addRow("OSC Address: ", self.send_osc_address_select)


        self.send_osc_button = QtWidgets.QPushButton()
        self.send_osc_button.setText("Send OSC")
        self.send_osc_button.clicked.connect(self.activate_osc_send)
        self.send_osc_button.setFixedSize(100, 50)
        self.send_osc_button.setCheckable(True)
        #self.send_osc_button.setStyleSheet("background-color : lightgrey")
        self.send_osc_box.layout().addRow(self.send_osc_button)

        self.tab_config.layout().addWidget(self.send_osc_box)


        ## MEASURE TAB
        #############################
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

        self.manualAngleBox = QtWidgets.QGroupBox("Set angle manually (Only visible when VIVE trackers are Qdisconnected)")
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
        self.positions_table.setModel(self.measurement_ref.positions_list)
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
        self.hp_controls_group.setAlignment(QtCore.Qt.AlignLeft)



        self.trigger_hp_measurement_button = QtWidgets.QPushButton("Trigger Headphone  \n Measurement")
        self.trigger_hp_measurement_button.clicked.connect(self.trigger_hp_measurement)
        self.trigger_hp_measurement_button.setFixedSize(QtCore.QSize(200, 100))
        self.hp_controls_group.layout().addWidget(self.trigger_hp_measurement_button)

        self.remove_hp_measurement_button = QtWidgets.QPushButton("Remove Last \n HP Measurement")
        self.remove_hp_measurement_button.clicked.connect(self.remove_hp_measurement)
        self.remove_measurement_button.setFixedSize(QtCore.QSize(200, 50))
        self.hp_controls_group.layout().addWidget(self.remove_hp_measurement_button)
        self.hp_controls_group.layout().addStretch()

        self.hp_measurement_count = QtWidgets.QLabel("")
        # self.hp_measurement_count.setFixedWidth(16)
        self.hp_controls_group.layout().addWidget(self.hp_measurement_count)



        self.tab_hpc.layout().addWidget(self.hp_controls_group)
        #self.plot_hpc_widget = PlotWidget()
        #self.tab_hpc.layout().addWidget(self.plot_hpc_widget)


        self.plot_hpirs = Figure()
        self.plot_hpirs.set_facecolor("none")
        self.plot_hpirs_canvas = FigureCanvas(self.plot_hpirs)
        self.plot_hpirs_canvas.setStyleSheet("background-color:transparent;")
        self.tab_hpc.layout().addWidget(self.plot_hpirs_canvas)

        self.reg_beta_layout = QtWidgets.QHBoxLayout()
        self.reg_beta_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.reg_beta_layout.addWidget(QtWidgets.QLabel("Reg Beta:"))

        self.regularization_beta_box = QtWidgets.QDoubleSpinBox()
        self.regularization_beta_box.setMaximum(1.0)
        self.regularization_beta_box.setSingleStep(0.05)
        self.regularization_beta_box.setValue(0.4)
        self.regularization_beta_box.setFixedWidth(100)
        self.regularization_beta_box.valueChanged.connect(self.set_regularization_beta)
        self.reg_beta_layout.addWidget(self.regularization_beta_box)

        self.tab_hpc.layout().addLayout(self.reg_beta_layout)

        self.plot_hpc = Figure()
        self.plot_hpc.set_facecolor('none')
        self.plot_hpc_canvas = FigureCanvas(self.plot_hpc)
        self.plot_hpc_canvas.setStyleSheet("background-color:transparent;")
        self.tab_hpc.layout().addWidget(self.plot_hpc_canvas)

        self.plot_hptf(np.array([]))
        self.plot_hpc_estimate(np.array([]), np.array([]))

        ## TAB REPRODUCTION

        self.player_box = QtWidgets.QGroupBox()
        self.player_box.setLayout(QtWidgets.QHBoxLayout())

        self.start_player_button = QtWidgets.QPushButton("Play")
        self.start_player_button.clicked.connect(measurement_ref.start_reproduction)
        self.player_box.layout().addWidget(self.start_player_button)

        self.stop_player_button = QtWidgets.QPushButton("Stop")
        self.stop_player_button.clicked.connect(measurement_ref.stop_reproduction)
        self.player_box.layout().addWidget(self.stop_player_button)

        self.tab_reproduction.layout().addWidget(self.player_box)

        ## Layout finalilzation

        self.gridLayout.addWidget(self.tabWidget, 0, 1, 3, 1)
        self.gridLayout.addWidget(self.vpWidget, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.device_status_widget, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.tracker_status_widget, 2, 0, 1, 1)
        self.gridLayout.addWidget(self.osc_status_box, 2, 0, 1, 1)

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

    def switch_trackers(self):
        self.measurement_ref.tracker.switch_trackers()
        if self.measurement_ref.tracker.trackers_switched:
            self.tracker1_label = QtWidgets.QLabel("Tracker 1:")
            self.tracker2_label = QtWidgets.QLabel("(Head) Tracker 2:")
        else:
            self.tracker1_label = QtWidgets.QLabel("(Head) Tracker 1:")
            self.tracker2_label = QtWidgets.QLabel("Tracker 2:")


    def update_tracker_status(self, status):
        self.tracker1_status_label.setText(status["tracker1"])
        self.tracker2_status_label.setText(status["tracker2"])

        if status["tracker1"] == "Tracking" and status["tracker2"] == "Tracking" \
                or self.measurement_ref.tracker.tracking_mode == "OSC_direct":
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


    # helper function to give all calibration functions the time delay
    def calibrate(self, calibration_function):
        interval = self.calibration_wait_time.value() * 1000
        QtCore.QTimer.singleShot(interval, calibration_function)

    def calibrate_orientation(self):
        if self.measurement_ref.tracker.calibrate_orientation():
            self.measurement_ref.measurement.play_sound(True)
            self.calibrate_orientation_label.setText("Calibrated")
        else:
            self.measurement_ref.measurement.play_sound(False)

    # NOTES on the calibrating of head dimensions:
    # left_ear and right_ear are for yielding the correct head center.
    # head_left and head_right are for yielding the correct anthropometric head width
    # head_front and head_right are for yielding the correct anthropometric head length

    def calibrate_left_ear(self):
        if self.measurement_ref.tracker.calibrate_headdimensions('left_ear', multiple_calls=False):
            self.calibrate_ear_left_label.setText(f"Calibrated")#, {self.measurement_ref.tracker.head_dimensions['ear_pos_l']}")
            self.measurement_ref.measurement.play_sound(True)
        else:
            self.measurement_ref.measurement.play_sound(False)
            if self.measurement_ref.tracker.head_dimensions['ear_pos_l'] is not None:
                self.calibrate_ear_left_label.setText(f"Recalibration failed")#, {self.measurement_ref.tracker.head_dimensions['ear_pos_l']}")

    def calibrate_right_ear(self):
        if self.measurement_ref.tracker.calibrate_headdimensions('right_ear', multiple_calls=False):
            self.calibrate_ear_right_label.setText(f"Calibrated")#, {self.measurement_ref.tracker.head_dimensions['ear_pos_r']}")
            self.measurement_ref.measurement.play_sound(True)
        else:
            self.measurement_ref.measurement.play_sound(False)
            if self.measurement_ref.tracker.head_dimensions['ear_pos_r'] is not None:
                self.calibrate_ear_right_label.setText(f"Recalibration failed")#, {self.measurement_ref.tracker.head_dimensions['ear_pos_r']}")


    def calibrate_head_left(self):
        if self.measurement_ref.tracker.calibrate_headdimensions('left'):
            self.measurement_ref.measurement.play_sound(True)
            self.calibrate_left_head_label.setText("Calibrated")
            if self.measurement_ref.tracker.head_dimensions['head_width'] is not None:
                self.head_width_label.setText(f"Head Width: {self.measurement_ref.tracker.head_dimensions['head_width']:.3f}")
        else:
            self.calibrate_left_head_label.setText("Calibration Failed")
            self.measurement_ref.measurement.play_sound(False)


    def calibrate_head_right(self):
        if self.measurement_ref.tracker.calibrate_headdimensions('right'):
            self.measurement_ref.measurement.play_sound(True)
            self.calibrate_right_head_label.setText("Calibrated")
            if self.measurement_ref.tracker.head_dimensions['head_width'] is not None:
                self.head_width_label.setText(f"Head Width: {self.measurement_ref.tracker.head_dimensions['head_width']:.3f}")
        else:
            self.calibrate_right_head_label.setText("Calibration Failed")
            self.measurement_ref.measurement.play_sound(False)


    def calibrate_head_front(self):
        if self.measurement_ref.tracker.calibrate_headdimensions('front'):
            self.measurement_ref.measurement.play_sound(True)
            self.calibrate_front_head_label.setText("Calibrated")
            if self.measurement_ref.tracker.head_dimensions['head_length'] is not None:
                self.head_length_label.setText(f"Head Length: {self.measurement_ref.tracker.head_dimensions['head_length']:.3f}")
        else:
            self.calibrate_front_head_label.setText("Calibration Failed")
            self.measurement_ref.measurement.play_sound(False)


    def calibrate_head_back(self):
        if self.measurement_ref.tracker.calibrate_headdimensions('back'):
            self.measurement_ref.measurement.play_sound(True)
            self.calibrate_back_head_label.setText("Calibrated")
            if self.measurement_ref.tracker.head_dimensions['head_length'] is not None:
                self.head_length_label.setText(f"Head Length: {self.measurement_ref.tracker.head_dimensions['head_length']:.3f}")
        else:
            self.calibrate_back_head_label.setText("Calibration Failed")


    def calibrate_acoustical_centre(self):
        if self.measurement_ref.tracker.calibrate_acoustical_center():
            self.measurement_ref.measurement.play_sound(True)
            self.calibrate_acoustical_center_label.setText(f'Calibrated')#, {self.measurement_ref.tracker.acoustical_center_pos}')
        else:
            self.measurement_ref.measurement.play_sound(False)



    def trigger_ref_measurement(self):
        interval = 0.5 * 1000
        QtCore.QTimer.singleShot(interval, self.measurement_ref.trigger_reference_measurement)

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

        #print("Data Table Selection: " + str(selected.row()))
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
            if index is self.tab_reproduction_index:
                self.measurement_ref.init_reproduction()
            else:
                self.measurement_ref.close_reproduction()

        except AttributeError:
            pass




    def clear_measurements(self):
        self.measurement_ref.delete_all_measurements()
        self.session_name.clear()

    def remove_measurement(self):
        indexes = self.positions_table_selection.selectedRows()
        for index in indexes:
            id = index.row()
            dialog = QtWidgets.QMessageBox
            ret = dialog.question(self.myMainWindow,'', "Are you sure you want to delete this measurement?", dialog.Yes | dialog.No)

            if ret == dialog.Yes:
                #print("Deleting Measurement " + str(id))
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
        ax.set_title("Headphone Compensation (Estimate)")
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
        self.headphone_name.clear()

    def warning_invalid_tracking(self, warning=True):
        palette = self.tracker_status_widget.palette()
        if warning:
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor('red'))
        else:
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor('grey'))


        self.tracker_status_widget.setPalette(palette)
        self.tracker_status_widget.setAutoFillBackground(True)
        self.tracker_status_widget.repaint()

    def select_tracking_input(self):
        radioButton = self.tracking_input_box.sender()
        if radioButton.isChecked():
            if radioButton.sourcename == "Vive":
                self.vivetracker_box.show()
                self.osc_config_box.hide()

                self.osc_status_box.hide()
                self.tracker_status_widget.show()

                self.measurement_ref.tracker.set_tracking_mode(radioButton.sourcename)

                self.send_osc_box.setEnabled(True)


            if radioButton.sourcename == "OSC_direct":
                self.vivetracker_box.hide()
                self.osc_config_box.show()

                self.tracker_status_widget.hide()
                self.osc_status_box.show()

                self.measurement_ref.tracker.set_tracking_mode(radioButton.sourcename)

                ip, port = self.measurement_ref.tracker.osc_input_server.get_current_ip_and_port()
                self.osc_ip_label.setText(f"Current Host IP: {ip}")
                self.osc_port_label.setText(f"OSC Server Port: {port}")

                self.send_osc_box.setEnabled(False)

                self.manualAngleBox.setVisible(False)


    def set_osc_status(self, osc_status):
        if osc_status:
            #self.osc_status_indicator.setStyleSheet("color: green")
            self.osc_status_indicator.setStyleSheet("QCheckBox::indicator"
                                                    "{"
                                                    "background-color : lightgreen;"
                                                    "}")
        else:
            #self.osc_status_indicator.setStyleSheet("color: white")
            self.osc_status_indicator.setStyleSheet("QCheckBox::indicator"
                                                    "{"
                                                    "background-color : white;"
                                                    "}")

    def activate_osc_send(self):

        checked = self.send_osc_button.isChecked()

        if self.send_osc_button.isChecked():
            if self.measurement_ref.start_osc_send(self.send_osc_ip_select.text(), self.send_osc_port_select.text(), self.send_osc_address_select.text()):
                self.send_osc_ip_select.setEnabled(False)
                self.send_osc_port_select.setEnabled(False)
                self.send_osc_address_select.setEnabled(False)
                self.tracking_input_OSC_direct.setEnabled(False)
            else:
                self.send_osc_button.setChecked(False)
        else:
            self.measurement_ref.stop_osc_send()
            self.send_osc_ip_select.setEnabled(True)
            self.send_osc_port_select.setEnabled(True)
            self.send_osc_address_select.setEnabled(True)
            self.tracking_input_OSC_direct.setEnabled(True)

    def update_sweep_parameters(self):
        try:
            self.measurement_ref.measurement.set_sweep_parameters(d_sweep_sec=float(self.sweeplength_sec.text()),
                                                                  d_post_silence_sec=float(self.post_silence_sec.text()),
                                                                  f_start=int(self.f_start.text()),
                                                                  f_end = int(self.f_end.text()),
                                                                  amp_db=float(self.amp_db.text()),
                                                                  fade_out_samples=int(self.fade_out_samples.text()))
        except ValueError:
            self.sweep_parameters_errormessage.setVisible(True)
            return

        self.sweep_parameters_errormessage.setVisible(False)
        self.sweep_parameters_dialog.close()

        return


class InstructionsDialogBox(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):

        instruction_text = \
            "1. Mount tracker T1 on listener head. The orientation and exact position are not important, as long as it stays fixed. \n\n" \
            "2. Check if tracker roles are correct by rotating tracker T2. The angles shouldn't change since only the position of tracker T2 is used. Switch tracker roles if necessary\n\n" \
            "3. Hold tracker T2 to both ears (bottom center on ear canal) and calibrate each ear. Tracker T2 orientation does not matter here, but from now on tracker T1 (on the listeners head) has to stay fixed & stable on the head.\n\n" \
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


    def plot_IRs(self, ir_l, ir_r, fs=48000, plot='waveform_log'):
        matplotlib.rcParams.update({'font.size': 5})

        self.plot2.clf()

        ax1 = self.plot2.add_subplot(211)
        ax1.clear()

        if plot=='waveform_log':
            t_vec = np.arange(0, np.size(ir_l)) / fs
            logwaveform = 20*np.log10(np.abs(ir_l))
            ax1.plot(t_vec, logwaveform)
            ax1.set_ylim([-120, np.max([np.max(logwaveform), 12])])
            ax1.set_xlabel('Seconds')
        elif plot=='waveform':
            t_vec = np.arange(0, np.size(ir_l)) / fs
            ax1.plot(t_vec, ir_l)
            ax1.set_xlabel('Seconds')
        elif plot=='spectrogram':
            _,_,_, cax = ax1.specgram(ir_l, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
            self.plot2.colorbar(cax).set_label('dB')

        ax2 = self.plot2.add_subplot(212)
        ax2.clear()

        if plot=='waveform_log':
            t_vec = np.arange(0, np.size(ir_r)) / fs
            logwaveform = 20 * np.log10(np.abs(ir_r))
            ax2.plot(t_vec, logwaveform)
            ax2.set_ylim([-120, np.max([np.max(logwaveform), 12])])
            ax2.set_xlabel('Seconds')
        elif plot == 'waveform':
            t_vec = np.arange(0, np.size(ir_r)) / fs
            ax2.plot(t_vec, ir_r)
        elif plot=='spectrogram':
            _,_,_, cax2 = ax2.specgram(ir_r, NFFT=self.spec_nfft, Fs=fs, noverlap=self.spec_noverlap, vmin=-200)
            self.plot2.colorbar(cax2).set_label('dB')

        self.plot2_canvas.draw()

