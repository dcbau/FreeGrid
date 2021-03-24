
import threading
import numpy as np
import socket

from pythonosc import dispatcher
from pythonosc import osc_server


class OSCInputServer(object):

    def __init__(self):

        # osc default settings
        self.ip = '127.0.0.1'
        self.port = 2222

        osc_dispatcher = dispatcher.Dispatcher()
        self.osc_identifier_angle = "/guided_hrtfs/angle"
        osc_dispatcher.map(self.osc_identifier_angle, self.direct_angle_input)

        self.server = osc_server.ThreadingOSCUDPServer(
            (self.ip, self.port), osc_dispatcher)

        self.server.allow_reuse_address = True

        self.angles = np.array([0, 0, 1])

        self.osc_timeout_sec = 1
        self.receiving = False

        self.timeout = threading.Timer(self.osc_timeout_sec, self.osc_stopped_receiving)

    def direct_angle_input(self, address, az, el, r):

        self.timeout.cancel()
        self.receiving = True

        self.angles[0] = az
        self.angles[1] = el
        self.angles[2] = r

        self.timeout = threading.Timer(self.osc_timeout_sec, self.osc_stopped_receiving)
        self.timeout.start()

    def osc_stopped_receiving(self):
        self.receiving = False

    def get_current_ip_and_port(self):
        ethernet_ip = socket.gethostbyname(socket.gethostname())
        return ethernet_ip, self.port

    def get_osc_identifiers(self):
        return self.osc_identifier_angle

    def get_current_angle(self):
        return self.angles

    def get_osc_receive_status(self):
        return self.receiving

    def start_listening(self):

        osc_thread = threading.Thread(target=self.server.serve_forever, name='OSC_THREAD')
        osc_thread.daemon = True
        osc_thread.start()

    def close(self):
        self.server.server_close()
        self.server.shutdown()
