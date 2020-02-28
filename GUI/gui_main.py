from PyQt5 import QtWidgets
from GUI.main_window import Ui_MainWindow

class gui_main(QtWidgets.QMainWindow):

    def __init__(self, measurement_ref):

        super().__init__()
        self.setWindowTitle('My Main Window')
        self._ui = None
        self.measurement_ref = measurement_ref

        self.loadMainGui()

    def loadMainGui(self):
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self, self.measurement_ref)

        self._ui.pushButton.clicked.connect(self._ui.trigger_measurement)

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).closeEvent(*args, **kwargs)
        self.measurement_ref.shutdown()

    def start_measurement(self):
        self.measurement_ref.single_measurement()
