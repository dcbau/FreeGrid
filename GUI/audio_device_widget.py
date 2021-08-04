from PyQt5 import QtCore, QtGui, QtWidgets
import pyaudio
import numpy as np
from measurement import AudioDeviceConfig

def query_hostapis(p):
    ## wrapper function to provice sounddevice-like api list from pyaudio
    apis = ()
    for i in range(p.get_host_api_count()):
        api = p.get_host_api_info_by_index(i)
        api = {
            'name': api['name'],
            'devices': [p.get_device_info_by_host_api_device_index(i, j)['index'] for j in range(api['deviceCount'])],
            'default_input_device': api['defaultInputDevice'],
            'default_output_device': api['defaultOutputDevice'],
        }

        apis = apis + tuple([api])

    return apis

def query_devices(p):
    ## wrapper function to provice sounddevice-like device list from pyaudio

    return tuple(p.get_device_info_by_index(i) for i in range(p.get_device_count()))



class AudioDeviceWidget(QtWidgets.QWidget):

    def __init__(self, measurement_ref):
        #super(AudioDeviceWidget, self).__init__(self)
        QtWidgets.QWidget.__init__(self)

        self.measurement_ref = measurement_ref

        self.p = measurement_ref.get_pa_handler()
        self.settings = AudioDeviceConfig(self.p)

        api_list = query_hostapis(self.p)
        textboxwidth = 120
        numboxwidth = 55
        self.api_box = QtWidgets.QComboBox()
        self.api_box.setFixedWidth(textboxwidth)
        self.output_devices_box = QtWidgets.QComboBox()
        self.output_devices_box.setFixedWidth(textboxwidth)
        self.input_devices_box = QtWidgets.QComboBox()
        self.input_devices_box.setFixedWidth(textboxwidth)
        self.samplerate_box = QtWidgets.QComboBox()
        self.samplerate_box.setFixedWidth(textboxwidth)
        self.use_feedback_loop = QtWidgets.QCheckBox()


        # channel layout as zero indexed channel numbers
        # output layout: [out_1, out_2, out_fb]
        # input layout: [in_left, in_right, in_fb]
        self.channel_layout_output = [0, 1, 2]
        self.channel_layout_input = [0, 1, 2]

        self.out_1_channel = QtWidgets.QComboBox()
        self.out_1_channel.setFixedWidth(numboxwidth)
        self.out_2_channel = QtWidgets.QComboBox()
        self.out_2_channel.setFixedWidth(numboxwidth)
        self.out_fb_channel = QtWidgets.QComboBox()
        self.out_fb_channel.setFixedWidth(numboxwidth)
        self.out_1_channel.activated.connect(self.set_channel_layout)
        self.out_2_channel.activated.connect(self.set_channel_layout)
        self.out_fb_channel.activated.connect(self.set_channel_layout)

        self.in_l_channel = QtWidgets.QComboBox()
        self.in_l_channel.setFixedWidth(numboxwidth)
        self.in_r_channel = QtWidgets.QComboBox()
        self.in_r_channel.setFixedWidth(numboxwidth)
        self.in_fb_channel = QtWidgets.QComboBox()
        self.in_fb_channel.setFixedWidth(numboxwidth)
        self.in_l_channel.activated.connect(self.set_channel_layout)
        self.in_r_channel.activated.connect(self.set_channel_layout)
        self.in_fb_channel.activated.connect(self.set_channel_layout)

        self.use_feedback_loop.stateChanged.connect(self.set_channel_layout)

        self.duplicate_channel_warning = QtWidgets.QLabel("Warning: Duplicate channel assignment!")

        self.api_box.activated.connect(self.update_api)
        self.output_devices_box.activated.connect(self.update_device)
        self.input_devices_box.activated.connect(self.update_device)
        self.samplerate_box.activated.connect(self.set_samplerate)

        self.current_api_id = self.settings.hostapi
        if self.current_api_id < 0:
            self.current_api_id = 0

        self.api_ids = []
        self.input_dev_ids = []
        self.output_dev_ids = []

        for id, api in enumerate(api_list):
            if len(api['devices']): #only add when devices are present
                self.api_box.addItem(api['name'])
                self.api_ids.append(id)
                # in case ASIO is available, prefer ASIO!
                if api['name'] == 'ASIO':
                    self.current_api_id = id

        self.api_box.setCurrentText(query_hostapis(self.p)[self.current_api_id]['name'])


        self.update_api()




        #self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
        layout = QtWidgets.QHBoxLayout()

        left_list = QtWidgets.QFormLayout()
        right_list = QtWidgets.QFormLayout()

        left_list.setVerticalSpacing(2)
        right_list.setVerticalSpacing(2)

        label1 = QtWidgets.QLabel("Select Audio Device:")
        headline_font = label1.font()
        headline_font.setBold(True)
        label1.setFont(headline_font)
        left_list.setAlignment(QtCore.Qt.AlignLeading)

        left_list.addRow(label1)
        left_list.addRow("Audio API", self.api_box)

        verticalSpacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        left_list.addItem(verticalSpacer)

        left_list.addRow("Input Device", self.input_devices_box)
        left_list.addRow("Output Device", self.output_devices_box)

        left_list.addItem(verticalSpacer)

        left_list.addRow("Samplerate:", self.samplerate_box)

        right_list.addRow(QtWidgets.QLabel("Set In/Out Channels:", font=headline_font))

        right_list.addRow(QtWidgets.QLabel("Output Excitation:"), self.out_1_channel)
        right_list.addRow(QtWidgets.QLabel("Output Excitation 2:"), self.out_2_channel)
        right_list.addRow(QtWidgets.QLabel("Output Feedback Loop:"), self.out_fb_channel)
        right_list.addRow(QtWidgets.QLabel("Input Left Ear Mic:"), self.in_l_channel)
        right_list.addRow(QtWidgets.QLabel("Input Right Ear Mic:"), self.in_r_channel)
        right_list.addRow(QtWidgets.QLabel("Input Feedback Loop:"), self.in_fb_channel)

        right_list.addItem(verticalSpacer)

        self.use_feedback_loop.setText("Use Feedback Loop if possible")
        right_list.addRow(self.use_feedback_loop)

        right_list.addItem(verticalSpacer)

        right_list.addItem(verticalSpacer)
        right_list.addRow(self.duplicate_channel_warning)
        self.duplicate_channel_warning.setVisible(False);
        self.duplicate_channel_warning.setFont(QtGui.QFont('Arial', 11))

        layout.addLayout(left_list)
        layout.addLayout(right_list)
        self.setLayout(layout)



    def update_api(self):
        # update the audio devices matching the API
        current_api = query_hostapis(self.p)[self.api_ids[self.api_box.currentIndex()]]
        self.settings.device = [max(current_api['default_input_device'], 0), max(current_api['default_output_device'], 0)]

        self.input_devices_box.clear()
        self.input_dev_ids.clear()
        self.output_devices_box.clear()
        self.output_dev_ids.clear()

        for device_id in current_api['devices']:
            device = query_devices(self.p)[device_id]
            display_name = f"{device['name']} ({device['maxInputChannels']} in, {device['maxOutputChannels']} out)"
            if device['maxInputChannels'] > 0:
                self.input_devices_box.addItem(display_name)
                self.input_dev_ids.append(device_id)
                if device_id == self.settings.device[0]:
                    self.input_devices_box.setCurrentText(display_name)
            if device['maxOutputChannels'] > 0:
                self.output_devices_box.addItem(display_name)
                self.output_dev_ids.append(device_id)
                if device_id == self.settings.device[1]:
                    self.output_devices_box.setCurrentText(display_name)

            if device_id == self.settings.device[0]:
                self.input_devices_box.setCurrentText(display_name)

            if device_id == self.settings.device[1]:
                self.output_devices_box.setCurrentText(display_name)

        self.update_device()

    def update_device(self, notify=True):

        in_id = self.input_devices_box.currentIndex()
        try:
            input_dev = self.input_dev_ids[in_id]
        except IndexError:
            input_dev = -1

        out_id = self.output_devices_box.currentIndex()
        try:
            output_dev = self.output_dev_ids[out_id]
        except IndexError:
            output_dev = -1
        self.settings.device = [input_dev, output_dev]

        self.update_available_samplerates(notify)

        # INPUT channels
        try:
            input_dev = query_devices(self.p)[self.settings.device[0]]
            num_in_ch = input_dev['maxInputChannels']
        except IndexError:
            num_in_ch = 0

        self.in_l_channel.clear()
        self.in_r_channel.clear()
        self.in_fb_channel.clear()

        if num_in_ch > 0:
            for channel in range(num_in_ch):
                self.in_l_channel.addItem(str(channel + 1))
            if self.channel_layout_input[0] == -1 or self.channel_layout_input[0] >= num_in_ch:
                self.channel_layout_input[0] = 0
            self.in_l_channel.setCurrentText(str(self.channel_layout_input[0] + 1))
        else:
            self.channel_layout_input[0] = -1

        if num_in_ch > 1:
            for channel in range(num_in_ch):
                self.in_r_channel.addItem(str(channel + 1))
            if self.channel_layout_input[1] == -1 or self.channel_layout_input[1] >= num_in_ch:
                self.channel_layout_input[1] = 1
            self.in_r_channel.setCurrentText(str(self.channel_layout_input[1] + 1))
        else:
            self.channel_layout_input[1] = -1

        if num_in_ch > 2:
            for channel in range(num_in_ch):
                self.in_fb_channel.addItem(str(channel + 1))
            if self.channel_layout_input[2] == -1 or self.channel_layout_input[2] >= num_in_ch:
                self.channel_layout_input[2] = 2
            self.in_fb_channel.setCurrentText(str(self.channel_layout_input[2] + 1))
        else:
            self.channel_layout_input[2] = -1


        # OUTPUT channels
        try:
            output_dev = query_devices(self.p)[self.settings.device[1]]
            num_out_ch = output_dev['maxOutputChannels']
        except IndexError:
            num_out_ch = 0

        self.out_1_channel.clear()
        self.out_2_channel.clear()
        self.out_fb_channel.clear()

        if num_out_ch > 0:
            for channel in range(num_out_ch):
                self.out_1_channel.addItem(str(channel+1))
            if self.channel_layout_output[0] == -1 or self.channel_layout_output[0] >= num_out_ch:
                self.channel_layout_output[0] = 0
            self.out_1_channel.setCurrentText(str(self.channel_layout_output[0] + 1))
        else:
            self.channel_layout_output[0] = -1

        if num_out_ch > 1:
            for channel in range(num_out_ch):
                self.out_2_channel.addItem(str(channel+1))
            if self.channel_layout_output[1] == -1 or self.channel_layout_output[1] >= num_out_ch:
                self.channel_layout_output[1] = 1
            self.out_2_channel.setCurrentText(str(self.channel_layout_output[1] + 1))
        else:
            self.channel_layout_output[1] = -1

        if num_out_ch > 2:
            for channel in range(num_out_ch):
                self.out_fb_channel.addItem(str(channel+1))
            if self.channel_layout_output[2] == -1 or self.channel_layout_output[2] >= num_out_ch:
                self.channel_layout_output[2] = 2
            self.out_fb_channel.setCurrentText(str(self.channel_layout_output[2] + 1))
        else:
            self.channel_layout_output[2] = -1

        self.set_channel_layout()

        self.measurement_ref.set_audio_settings(self.settings)

    def update_available_samplerates(self, notify=True):
        # define supported samplerates
        samplerates = [44100, 48000, 88200, 96000]
        
        # add the current devices default samplerate
        default_input_device = query_devices(self.p)[self.settings.device[0]]
        default_output_device = query_devices(self.p)[self.settings.device[1]]
        try:
            samplerates.append(int(default_input_device['default_samplerate']))
            samplerates.append(int(default_output_device['default_samplerate']))
        except:
            pass

        samplerates = list(set(samplerates))
        samplerates.sort()

        # check if both devices support the samplerates
        for i in range(np.size(samplerates)):
            try:
                self.p.is_format_supported(rate=samplerates[i], input_device=self.settings.device[0], input_format=pyaudio.paInt16, input_channels=1)
                self.p.is_format_supported(rate=samplerates[i], output_device=self.settings.device[1], output_format=pyaudio.paInt16, output_channels=1)
            except ValueError:
                samplerates.remove(samplerates[i])

        if len(samplerates) == 0:
            print("Audio device does not support samplerates 44.1, 48, 88.2 or 96")

        self.samplerate_box.clear()
        for fs in samplerates:
            self.samplerate_box.addItem(str(fs))

        if 48000 in samplerates:
            self.samplerate_box.setCurrentText(str(48000))
        else:
            self.samplerate_box.setCurrentText(str(samplerates[0]))

        self.set_samplerate(notify=False)

    # called on selection event
    def set_samplerate(self, notify=True):
        self.settings.samplerate = int(self.samplerate_box.currentText())
        if notify:
            self.measurement_ref.set_audio_settings(self.settings)

    # TODO: add notify flag, merge Measurement.set_channel_layout() and Measurement.set_audio_settings() to a single function
    def set_channel_layout(self):

        out1 = self.out_1_channel.currentIndex()
        out2 = self.out_2_channel.currentIndex()
        out_fb = self.out_fb_channel.currentIndex()

        self.channel_layout_output = [out1, out2, out_fb]

        in_l = self.in_l_channel.currentIndex()
        in_r = self.in_r_channel.currentIndex()
        in_fb = self.in_fb_channel.currentIndex()

        self.channel_layout_input = [in_l, in_r, in_fb]

        duplicates =  self.check_for_channel_duplicates(self.channel_layout_input)
        duplicates += self.check_for_channel_duplicates(self.channel_layout_output)

        self.duplicate_channel_warning.setVisible(bool(duplicates))

        if not self.use_feedback_loop.isChecked():
            self.channel_layout_output[2] = -1
            self.channel_layout_input[2] = -1
        else:
            self.channel_layout_output[2] = self.out_fb_channel.currentIndex()
            self.channel_layout_input[2] = self.in_fb_channel.currentIndex()


        self.measurement_ref.set_channel_layout(self.channel_layout_input, self.channel_layout_output)

    def check_for_channel_duplicates(self, channel_list):
        '''Returns True if a valid hardware channel is assigned for multiple in/out channels. Invalid channel
        assignments (-1) are ignored '''
        if len(channel_list) != len(set(channel_list)):
            if channel_list.count(-1) < 2:
                return True
            else:
                return False
        else:
            return False

    def get_current_channel_layout(self):
        if not self.use_feedback_loop.isChecked():
            self.channel_layout_output[2] = -1
            self.channel_layout_input[2] = -1

        return self.channel_layout_input, self.channel_layout_output
