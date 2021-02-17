from PyQt5 import QtWidgets
import sys

from GUI.gui_main import gui_main
from measurement_controller import MeasurementController

def main():

    app = QtWidgets.QApplication(sys.argv)

    measurement_controller = MeasurementController()

    gui = gui_main(measurement_controller)
    gui.show()

    gui._ui.retranslateUi(gui)

    sys.exit(app.exec_())



if __name__ == '__main__':
    main()
