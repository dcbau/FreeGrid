from PyQt5 import QtWidgets, QtCore
import sys

from GUI.main_window import UiMainWindow
from measurement_controller import MeasurementController
import warnings

# from GUI import breeze_resources

# plotting a wavefile logarithmically with zeros in it will warn about this
warnings.filterwarnings("ignore", message='divide by zero encountered in log10')


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("HH")

    # file = QtCore.QFile(":/dark.qss")
    # file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
    # stream = QtCore.QTextStream(file)
    # app.setStyleSheet(stream.readAll())


    measurement_controller = MeasurementController()

    gui = UiMainWindow(measurement_controller)

    # gui.setWindowTitle("HHHH")

    gui.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
