# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets
from GUI.PicButton import PicButton
from GUI.vispyWidget import VispyCanvas, VispyWidget
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib


class UiMainWindow(object):



    def setupUi(self, MainWindow, measurement_ref):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1100, 900)

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
        self.tabWidget.addTab(self.tab_measure, "")
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)



        self.vpWidget = QtWidgets.QWidget(self.tab_measure)
        self.vpWidget.setObjectName("vpWidget")
        self.vpWidget.setLayout(QtWidgets.QVBoxLayout())
        self.vispy_canvas = VispyCanvas(measurement_ref)
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
        self.pushButton.clicked.connect(self.measurement_ref.trigger_measurement)

        self.calibrateButton = QtWidgets.QPushButton(self.tab_measure)
        self.calibrateButton.setText("Calibrate")
        self.calibrateButton.setObjectName("calibrateButton")
        self.calibrateButton.clicked.connect(self.measurement_ref.tracker.calibrate)

        self.switchTrackersButton = QtWidgets.QPushButton(self.tab_measure)
        self.switchTrackersButton.setText("Switch Trackers")
        self.switchTrackersButton.setObjectName("switchTrackersButton")
        self.switchTrackersButton.clicked.connect(self.measurement_ref.tracker.switch_trackers)

        self.azimuthBox = QtWidgets.QSpinBox(self.tab_measure)
        self.azimuthBox.setMaximum(359)
        self.azimuthBox.valueChanged.connect(self.manual_update_az)
        self.elevationBox = QtWidgets.QSpinBox(self.tab_measure)

        self.elevationBox.setMaximum(90)
        self.elevationBox.setMinimum(-90)
        self.elevationBox.valueChanged.connect(self.manual_update_el)

        self.az_label = QtWidgets.QLabel(self.tab_measure)
        self.az_label.setText("Azimuth °")

        self.el_label = QtWidgets.QLabel(self.tab_measure)
        self.el_label.setText("Elevation °")

        self.plot_tab_widget = QtWidgets.QTabWidget(self.tab_measure)
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
        self.plot_tab_widget.addTab(self.tab_rec, "")
        self.tab_ir = QtWidgets.QWidget()
        self.tab_ir.setEnabled(True)
        self.tab_ir.setObjectName("tab_ir")
        self.plot_tab_widget.addTab(self.tab_ir, "")

        self.plotWidget1 = QtWidgets.QWidget(self.tab_rec)
        self.plotWidget1.setObjectName("plotWidget")
        self.plotWidget1.setLayout(QtWidgets.QVBoxLayout())

        self.plot1 = Figure()
        self.plot1_canvas = FigureCanvas(self.plot1)
        self.plotWidget1.layout().addWidget(self.plot1_canvas)

        self.plotWidget2 = QtWidgets.QWidget(self.tab_ir)
        self.plotWidget2.setObjectName("plotWidget")
        self.plotWidget2.setLayout(QtWidgets.QVBoxLayout())

        self.plot2 = Figure()
        self.plot2_canvas = FigureCanvas(self.plot2)
        self.plotWidget2.layout().addWidget(self.plot2_canvas)






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

        self.measurement_ref.register_gui_handler(self)

        print('FINISH SETUP')





    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_config), _translate("MainWindow", "Configure"))
        self.pushButton.setText(_translate("MainWindow", "PushButton"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_measure), _translate("MainWindow", "Measure"))
        self.plot_tab_widget.setTabText(self.plot_tab_widget.indexOf(self.tab_rec), _translate("MainWindow", "REC"))
        self.plot_tab_widget.setTabText(self.plot_tab_widget.indexOf(self.tab_ir), _translate("MainWindow", "IR"))


        bounds = QtCore.QRect(self.tabWidget.geometry())
        leftpane = QtCore.QRect(bounds)
        leftpane.setWidth(bounds.width() / 2)
        rightpane = leftpane.translated(bounds.width() / 2, 0)
        leftpane.adjust(20, 20, -40, -40)
        rightpane.adjust(20, 20, -40, -40)

        vispybox = QtCore.QRect(leftpane)
        size = leftpane.width() if leftpane.width() < leftpane.height() else leftpane.height()
        vispybox.setHeight(size)

        plotbox = QtCore.QRect(rightpane)
        size = rightpane.width() if rightpane.width() < rightpane.height() else rightpane.height()
        plotbox.setHeight(size)

        self.vpWidget.setGeometry(vispybox)
        self.sliderTheta.setGeometry(self.vpWidget.frameGeometry().x(),
                                     self.vpWidget.frameGeometry().bottom(),
                                     self.vpWidget.frameGeometry().width(),
                                     20)
        self.sliderPhi.setGeometry(self.vpWidget.frameGeometry().right(),
                                   self.vpWidget.frameGeometry().y(),
                                   20,
                                   self.vpWidget.frameGeometry().height())
        size = 80
        self.pushButton.setGeometry(plotbox.x(),
                                    plotbox.bottom() + 30,
                                    80,
                                    80)

        size = vispybox.width()*0.6
        self.calibrateButton.setGeometry(vispybox.center().x() - size/2,
                                         self.sliderTheta.geometry().bottom(),
                                         size,
                                         40)
        self.switchTrackersButton.setGeometry(vispybox.center().x() - size / 2,
                                              self.calibrateButton.geometry().bottom() + 5,
                                              size,
                                              40)
        self.az_label.setGeometry(vispybox.x(),
                                  self.switchTrackersButton.geometry().bottom() + 5,
                                  80,
                                  20)

        self.el_label.setGeometry(vispybox.x(),
                                  self.az_label.geometry().bottom() + 5,
                                  80,
                                  20)

        self.azimuthBox.setGeometry(self.az_label.geometry().right() + 5,
                                    self.az_label.geometry().y(),
                                    80,
                                    20)

        self.elevationBox.setGeometry(self.el_label.geometry().right() + 5,
                                    self.el_label.geometry().y(),
                                    80,
                                    20)

        self.plot_tab_widget.setGeometry(plotbox)
        self.plotWidget1.setGeometry(10,10, plotbox.width()-20, plotbox.height()-20)
        self.plotWidget2.setGeometry(10,10, plotbox.width()-20, plotbox.height()-20)




    def manual_update_az(self):
        self.measurement_ref.tracker.fallback_angle[0] = self.azimuthBox.value()

    def manual_update_el(self):
        self.measurement_ref.tracker.fallback_angle[1] = self.elevationBox.value()

    def add_measurement_point(self, az, el):
        self.vispy_canvas.meas_points.add_point(az, el)


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