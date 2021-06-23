from PyQt5 import QtCore, QtGui, QtWidgets
import sounddevice as sd

class AudioDeviceWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(AudioDeviceWidget, self).__init__(*args, **kwargs)

        api_list = sd.query_hostapis()
        self.api_box = QtWidgets.QComboBox()
        self.output_devices_box = QtWidgets.QComboBox()
        self.input_devices_box = QtWidgets.QComboBox()

        devs = self.get_names_of_default_devices()
        self.label_out_exc = QtWidgets.QLabel(devs['out_excitation'])
        self.label_out_exc_2 = QtWidgets.QLabel(devs['out_excitation_2'])
        self.label_out_fb = QtWidgets.QLabel(devs['out_feedback'])
        self.label_in_left = QtWidgets.QLabel(devs['in_left'])
        self.label_in_right = QtWidgets.QLabel(devs['in_right'])
        self.label_in_fb = QtWidgets.QLabel(devs['in_feedback'])

        self.api_box.currentTextChanged.connect(self.update_api)
        self.output_devices_box.activated.connect(self.update_device)
        self.input_devices_box.activated.connect(self.update_device)

        self.current_api_id = sd.default.hostapi

        self.input_dev_ids = []
        self.output_dev_ids = []

        for id, api in enumerate(api_list):
            self.api_box.addItem(api['name'])
            # in case ASIO is available, prefer ASIO!
            if api['name'] == 'ASIO':
                sd.default.device = [api['default_input_device'], api['default_output_device']]
                self.current_api_id = id
                #api_box.setCurrentText('ASIO')

        self.api_box.setCurrentText(sd.query_hostapis(self.current_api_id)['name'])




        #self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
        layout = QtWidgets.QFormLayout()
        layout.addRow("Audio API", self.api_box)
        layout.addRow("Input Device", self.input_devices_box)
        layout.addRow("Output Device", self.output_devices_box)

        verticalSpacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(verticalSpacer)

        layout.addRow(QtWidgets.QLabel("Output Excitation:"), self.label_out_exc)
        layout.addRow(QtWidgets.QLabel("Output Excitation 2:"), self.label_out_exc_2)
        layout.addRow(QtWidgets.QLabel("Output Feedback Loop:"), self.label_out_fb)
        layout.addRow(QtWidgets.QLabel("Input Left Ear Mic:"), self.label_in_left)
        layout.addRow(QtWidgets.QLabel("Input Right Ear Mic:"), self.label_in_right)
        layout.addRow(QtWidgets.QLabel("Input Feedback Loop:"), self.label_in_fb)


        self.setLayout(layout)

    def update_api(self):
        # update the audio devices matching the API
        current_api = sd.query_hostapis(self.api_box.currentIndex())
        sd.default.device = [current_api['default_input_device'], current_api['default_output_device']]

        self.input_devices_box.clear()
        self.output_devices_box.clear()

        for device_id in current_api['devices']:
            device = sd.query_devices(device_id)
            display_name = f"{device['name']} ({device['max_input_channels']} in, {device['max_output_channels']} out)"
            if device['max_input_channels'] > 0:
                self.input_devices_box.addItem(display_name)
                self.input_dev_ids.append(device_id)
                if device_id == sd.default.device[0]:
                    self.input_devices_box.setCurrentText(display_name)
            if device['max_output_channels'] > 0:
                self.output_devices_box.addItem(display_name)
                self.output_dev_ids.append(device_id)
                if device_id == sd.default.device[1]:
                    self.output_devices_box.setCurrentText(display_name)

            if device_id == sd.default.device[0]:
                self.input_devices_box.setCurrentText(display_name)

            if device_id == sd.default.device[1]:
                self.output_devices_box.setCurrentText(display_name)

        self.update_device()

    def update_device(self):

        in_id = self.input_devices_box.currentIndex()
        print(f"Input Dev: {in_id}")

        input_dev = self.input_dev_ids[in_id]
        out_id = self.output_devices_box.currentIndex()
        output_dev = self.output_dev_ids[out_id]
        print(f"Output Dev: {out_id}")
        sd.default.device = [input_dev, output_dev]


        devs = self.get_names_of_default_devices()
        self.label_out_exc.setText(devs['out_excitation'])
        self.label_out_exc_2.setText(devs['out_excitation_2'])
        self.label_out_fb.setText(devs['out_feedback'])
        self.label_in_left.setText(devs['in_left'])
        self.label_in_right.setText(devs['in_right'])
        self.label_in_fb.setText(devs['in_feedback'])





    def get_names_of_default_devices(self):
        try:
            input_dev = sd.query_devices(sd.default.device[0])
            output_dev = sd.query_devices(sd.default.device[1])

            out_excitation = output_dev['name'] + ", Ch1"
            num_in_ch = input_dev['max_input_channels']
            num_out_ch = output_dev['max_output_channels']

        except sd.PortAudioError:
            num_in_ch = 0
            num_out_ch = 0


        device_strings = {
            "out_excitation": "Unavailable",
            "out_excitation_2": "Unavailable",
            "out_feedback": "Unavailable/Disabled",
            "in_left": "Unavailable",
            "in_right": "Unavailable",
            "in_feedback": "Unavailable/Disabled"
        }
        if num_out_ch > 0:
            device_strings["out_excitation"] = output_dev['name'] + ", Ch1"
        if num_out_ch > 1:
            device_strings["out_excitation_2"] = output_dev['name'] + ", Ch2"
        if num_in_ch > 0:
            device_strings["in_left"] = input_dev['name'] + ", Ch1"
        if num_in_ch > 1:
            device_strings["in_right"] = input_dev['name'] + ", Ch2"
        if num_in_ch > 2 and num_out_ch > 2:
            device_strings["in_feedback"] = input_dev['name'] + ", Ch3"
            device_strings["out_feedback"] = output_dev['name'] + ", Ch3"

        return device_strings



