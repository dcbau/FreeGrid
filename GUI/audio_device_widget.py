from PyQt5 import QtCore, QtGui, QtWidgets
import sounddevice as sd

class AudioDeviceWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(AudioDeviceWidget, self).__init__(*args, **kwargs)

        api_list = sd.query_hostapis()
        self.api_box = QtWidgets.QComboBox()
        self.devices_box = QtWidgets.QComboBox()

        self.api_box.currentTextChanged.connect(self.update_apis)
        self.current_api_id = sd.default.hostapi
        for id, api in enumerate(api_list):
            self.api_box.addItem(api['name'])
            # in case ASIO is present, prefer ASIO!
            if api['name'] == 'ASIO':
                sd.default.device = [api['default_input_device'], api['default_output_device']]
                self.current_api_id = id
                #api_box.setCurrentText('ASIO')

        self.api_box.setCurrentText(sd.query_hostapis(self.current_api_id)['name'])




        #self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
        layout = QtWidgets.QFormLayout()
        layout.addRow("Audio API", self.api_box)
        layout.addRow("Audio Device", self.devices_box)
        # layout.addRow(QtWidgets.QLabel("Output Excitation 2:"), "")
        # layout.addRow(QtWidgets.QLabel("Output Feedback Loop:"), "")
        # layout.addRow(QtWidgets.QLabel("Input Left Ear Mic:"), "self.label_in_left")
        # layout.addRow(QtWidgets.QLabel("Input Right Ear Mic:"), "label_in_right")
        # layout.addRow(QtWidgets.QLabel("Input Feedback Loop:"), "self.label_in_fb")

        self.setLayout(layout)

    def update_apis(self):
        # update the audio devices matching the API
        current_api = sd.query_hostapis(self.api_box.currentIndex())
        self.devices_box.clear()
        for device_id in current_api['devices']:
            self.devices_box.addItem(sd.query_devices(device_id)['name'])

