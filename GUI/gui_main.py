from PyQt5 import QtWidgets
from GUI.main_window import UiMainWindow

class gui_main(QtWidgets.QMainWindow):

    def __init__(self, measurement_ref):

        super().__init__()
        self.setWindowTitle('My Main Window')
        self._ui = None
        self.measurement_ref = measurement_ref

        self.loadMainGui()


    def loadMainGui(self):
        self._ui = UiMainWindow()
        self._ui.setupUi(self, self.measurement_ref)

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).closeEvent(*args, **kwargs)

    def resizeEvent(self, event):
        self._ui.retranslateUi(self)


