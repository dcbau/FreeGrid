from grid_improving.grid_filling import *

from PyQt5 import QtWidgets
import sys

from GUI.gui_main import gui_main
from measurement import Measurement

def main():

    app = QtWidgets.QApplication(sys.argv)

    measurement = Measurement()

    gui = gui_main(measurement)
    gui.show()

    sys.exit(app.exec_())



if __name__ == '__main__':
    main()
