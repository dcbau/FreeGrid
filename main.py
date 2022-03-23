from PyQt5 import QtWidgets, QtCore
import sys

from GUI.main_window import UiMainWindow
from measurement_controller import MeasurementController
import warnings

import pkg_resources

pyqt5_version = pkg_resources.get_distribution("PyQT5").version
try:
    vispy_version = pkg_resources.get_distribution("vispy").version
except pkg_resources.DistributionNotFound:
    vispy_version = "Not found"
openVR_version = pkg_resources.get_distribution("openvr").version
matplotlib_version = pkg_resources.get_distribution("matplotlib").version
pythonosc_version = pkg_resources.get_distribution("python-osc").version
pyquaternion_version = pkg_resources.get_distribution("pyquaternion").version
sounddevice_version = pkg_resources.get_distribution("sounddevice").version

print(f"External Packages: PyQT5: {pyqt5_version}, vispy: {vispy_version}, pyopenvr: {openVR_version}, python-sounddevice: {sounddevice_version}, Matplotlib: {matplotlib_version}, python-osc: {pythonosc_version}, pyquaternion: {pyquaternion_version}")



# plotting a wavefile logarithmically with zeros in it will warn about this
warnings.filterwarnings("ignore", message='divide by zero encountered in log10')


def main():
    app = QtWidgets.QApplication(sys.argv)

    measurement_controller = MeasurementController()

    gui = UiMainWindow(measurement_controller)

    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
