# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_window.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets
from GUI.PicButton import PicButton
from GUI.glWidget import glWidget
from GUI.vispyWidget import VispyCanvas, VispyWidget
import threading
import numpy as np
from grid_filling import angularDistance

class Ui_MainWindow(object):
    def setupUi(self, MainWindow, measurement_ref):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 500)

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
        self.tab = QtWidgets.QWidget()
        self.tab.setEnabled(True)
        self.tab.setObjectName("tab")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setEnabled(True)
        self.tab_2.setObjectName("tab_2")



        self.vpWidget = VispyWidget(self.tab_2)
        self.vpWidget.setGeometry(QtCore.QRect(10, 10, 300, 300))
        self.vpWidget.setObjectName("vpWidget")
        self.vpWidget.setLayout(QtWidgets.QVBoxLayout())
        #self.vpWidget.clic.connect(self.vispy_canvas.update_angle())

        self.vispy_canvas = VispyCanvas()
        #QtCore.QObject.connect(self.vpWidget, SIGNAL(""), b2_clicked)
        #self.vpWidget.mousePressEvent.connect(self.vispy_canvas.update_angle())

        self.vpWidget.layout().addWidget(self.vispy_canvas.native)


        self.sliderTheta = QtWidgets.QSlider(self.tab_2)
        self.sliderTheta.setGeometry(QtCore.QRect(10, 310, 300, 30))
        self.sliderTheta.setOrientation(QtCore.Qt.Horizontal)
        self.sliderTheta.setObjectName("sliderTheta")
        self.sliderTheta.valueChanged.connect(self.vispy_canvas.update_theta)

        self.sliderPhi = QtWidgets.QSlider(self.tab_2)
        self.sliderPhi.setGeometry(QtCore.QRect(310, 10, 30, 300))
        self.sliderPhi.setOrientation(QtCore.Qt.Vertical)
        self.sliderPhi.setObjectName("sliderPhi")
        self.sliderPhi.valueChanged.connect(self.vispy_canvas.update_phi)

        #self.vispy_canvas.create_native()
        #self.vispy_canvas.native.setParent(self.tab_2)
        #self.vispy_canvas.show()
        #self.vispy_canvas.start()

        #icon = QtGui.QIcon()
        #icon.addPixmap(QtGui.QPixmap("Resources/start_button_x4.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        pixmap = QtGui.QPixmap("Resources/start_button_x2.png")
        pixmap_mouseover = QtGui.QPixmap("Resources/start_button_x2_mouseover.png")
        pixmap_pressed = QtGui.QPixmap("Resources/start_button_x2_pressed.png")

        #elf.pushButton = QtWidgets.QPushButton(self.tab_2)
        self.pushButton = PicButton(pixmap, pixmap_mouseover, pixmap_pressed, self.tab_2)
        self.pushButton.setGeometry(QtCore.QRect(350, 350, 189/2, 187/2))
        self.pushButton.setObjectName("pushButton")
        #self.pushButton.clicked.connect(self.vispy_canvas.inc_angle)

        self.calibrateButton = QtWidgets.QPushButton(self.tab_2)
        self.calibrateButton.setGeometry(QtCore.QRect(30, 350, 70, 30))
        self.calibrateButton.setText("Calibrate")
        self.calibrateButton.clicked.connect(self.vispy_canvas.calibrate)

        self.output_device_label = QtWidgets.QLabel(self.tab_2)
        self.output_device_label.setGeometry(350, 10, 150, 20)
        self.output_device_label.setText("Output Device")

        self.comboBoxOutput = QtWidgets.QComboBox(self.tab_2)
        outputDevices = measurement_ref.get_output_devices()
        for dev in outputDevices:
            self.comboBoxOutput.addItem(dev['name'])
        self.comboBoxOutput.setGeometry(350, 30, 200, 30)
        self.comboBoxOutput.activated[str].connect(self.select_output_device)
        #self.comboBoxOutput.setCurrentText(self.measurement_ref.get_current_output_device())
        # self.comboBoxOutputChannels = QtWidgets.QComboBox(self.tab_2)
        # self.comboBoxOutputChannels.setGeometry(350, 60, 70, 30)
        # self.get_output_channels()

        self.input_device_label = QtWidgets.QLabel(self.tab_2)
        self.input_device_label.setGeometry(350, 100, 150, 20)
        self.input_device_label.setText("Input Device")

        self.comboBoxInput = QtWidgets.QComboBox(self.tab_2)
        inputDevices = measurement_ref.get_input_devices()
        for dev in inputDevices:
            self.comboBoxInput.addItem(dev['name'])
        self.comboBoxInput.setGeometry(350, 120, 200, 30)
        self.comboBoxInput.activated[str].connect(self.select_input_device)
        #self.comboBoxInput.setCurrentText(self.measurement_ref.get_current_input_device())
        #
        # self.comboBoxInputChannels_L = QtWidgets.QComboBox(self.tab_2)
        # self.comboBoxInputChannels_L.setGeometry(350, 150, 70, 30)
        # self.comboBoxInputChannels_R = QtWidgets.QComboBox(self.tab_2)
        # self.comboBoxInputChannels_R.setGeometry(450, 150, 70, 30)
        # self.get_input_channels()


        self.tabWidget.addTab(self.tab_2, "")
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
        self.measurement_history = []

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Configure"))
        self.pushButton.setText(_translate("MainWindow", "PushButton"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Measure"))

    def select_output_device(self, name):
        self.measurement_ref.set_output_device_by_name(name)

    def select_input_device(self, name):
        self.measurement_ref.set_input_device_by_name(name)


    def timer_callback(self):
        if(self.measurement_running_flag == True):
            #check for variance
            tolerance_angle = 1 # (degree)
            tolerance_radius = 0.1 # (meter)
            az, el, r = self.vispy_canvas.tracker.getRelativePosition()
            if(angularDistance(az, el, self.measurement_position[0], self.measurement_position[1]) > tolerance_angle
                    and abs(r - self.measurement_position) > tolerance_radius):
                self.measurement_valid = False
                self.vispy_canvas.tracker.trigger_haptic_impulse()


        else:
            if(self.vispy_canvas.tracker.checkForTriggerEvent()):
                az, el, r = self.vispy_canvas.tracker.getRelativePosition()
                self.measurement_position = np.array([az, el, r])
                t1 = MeasurementHelperThread(target=self.measurement_ref.single_measurement, ref=self)
                self.measurement_running_flag = True
                self.measurement_valid = True
                t1.start()

    def stop_measurement(self):
        self.measurement_running_flag = False

        self.measurement_ref.save_single_measurement(self.measurement_valid,
                                                     self.measurement_position[0],
                                                     self.measurement_position[1],
                                                     self.measurement_position[2])

        if not self.measurement_history:
            # if it is the first measurement, there´s nothing to append
            self.measurement_history = self.measurement_position
        else:
            self.measurement_history = np.append(self.measurement_history, self.measurement_position)

class MeasurementHelperThread(threading.Thread):
    def __init__(self, target, ref):
        self._starget = target
        self._ref = ref
        threading.Thread.__init__(self)

    def run(self):
        self._starget()
        self._ref.stop_measurement()

