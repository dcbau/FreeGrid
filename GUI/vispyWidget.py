import sys
import numpy as np

from vispy import app, gloo, geometry
from vispy.util.transforms import perspective, translate, rotate
from vispy.geometry.generation import create_sphere
from vispy.color.colormap import get_colormaps

from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import  *
from PyQt5.QtWidgets import *

import tracker_manager

vertex = """
uniform mat4   u_model;         // Model matrix
uniform mat4   u_view;          // View matrix
uniform mat4   u_projection;    // Projection matrix
attribute vec3 a_position;
attribute vec4 a_sourceColour;
varying vec4 v_destinationColour;
void main()
{
    v_destinationColour = a_sourceColour;
    gl_Position = u_projection * u_view * u_model * vec4(a_position, 1.0);
}
"""

# The other shader we need to create is the fragment shader.
# It lets us control the pixels' color.
fragment = """
varying vec4 v_destinationColour;
void main()
{
    gl_FragColor = v_destinationColour;
}
"""
class VispyWidget(QWidget):

    clicked = pyqtSignal()

    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.color = QColor(0,0,0)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), QBrush(self.color))
        painter.end()

    def mousePressEvent(self, event):

        self.clicked.emit()






class VispyCanvas(app.Canvas):

    def __init__(self, theta=90.0, phi=90.0, z=6.0):


        self.calibrationPosition = np.empty([3, 4])

        self.tracker = tracker_manager.TrackerManager()

        app.Canvas.__init__(self, size=(200, 200), title='plot3d',
                            keys='interactive')
        #app.use_app('PyQt5')

        N = 1000
        self.data = np.c_[
            np.sin(np.linspace(-10, 10, N) * np.pi),
            np.cos(np.linspace(-10, 10, N) * np.pi),
            np.linspace(-2, 2, N)]

        #self.data = self.make_plane_grid(5, 9)
        self.sphereradius = 1.5
        self.boxsize = 0.4
        self.data, self.indices, self.line_indices = self.sphere(self.sphereradius, 15, 20)

        num_vertices = int(self.data.size / 3)
        self.data_color = np.zeros([num_vertices, 4])
        for i in range(num_vertices):
            self.data_color[i][0] = 0.0
            self.data_color[i][1] = 0.0
            self.data_color[i][2] = 0.0
            self.data_color[i][3] = 0.2


        self.data_color = self.data_color.astype(np.float32)
        self.data = self.data.astype(np.float32)

        #self.data2, self.indices = self.sphere(2, 20, 20)
        self.indices = gloo.IndexBuffer(self.indices)
        self.line_indices = gloo.IndexBuffer(self.line_indices)

        self.data2, self.indices2 = self.make_box_lines(self.boxsize)
        self.indices2 = gloo.IndexBuffer(self.indices2)
        num_vertices = int(self.data2.size / 3)
        self.data_color2 = np.zeros([num_vertices, 4])
        for i in range(num_vertices):
            self.data_color2[i][0] = 0.0
            self.data_color2[i][1] = 0.0
            self.data_color2[i][2] = 0.0
            self.data_color2[i][3] = 1.0
            #self.data2 = gloo.VertexBuffer(self.data2)

        self.data_color2 = self.data_color2.astype(np.float32)

        #self.data2 = self.data
        #indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
        #self.indices = gloo.IndexBuffer(self.indices)

        testangles = np.array([[0, 90],
                              [0, 45],
                              [135, 90],
                              [180, 180]])

        num_vertices = testangles.size
        self.data3 = np.zeros([num_vertices, 3], dtype=np.float32)
        self.data_color3 = np.zeros([num_vertices, 4], dtype=np.float32)

        r = 1.5
        for i in range(int(testangles.size/2)):
            az = testangles[i][0]
            el = testangles[i][1]
            self.data3[i][0] = r * np.sin(el) * np.cos(az)
            self.data3[i][1] = r * np.cos(el)
            self.data3[i][2] = r * np.sin(el) * np.sin(az)

            self.data_color3[i][0] = 1.0
            self.data_color3[i][1] = 0.0
            self.data_color3[i][2] = 0.0
            self.data_color3[i][3] = 1.0





        program = gloo.Program(vert=vertex, frag=fragment)
        #program.bind(self.data2)

        # initialize 3D view
        view = np.eye(4, dtype=np.float32)
        model = np.eye(4, dtype=np.float32)
        projection = np.eye(4, dtype=np.float32)

        # update program
        program['u_model'] = model
        program['u_view'] = view
        program['u_projection'] = projection
        program['a_position'] = gloo.VertexBuffer(self.data)


        # bind
        self.program = program
        self.theta = theta
        self.phi = phi
        self.z = z

        # config
        gloo.set_viewport(0, 0, *self.physical_size)
        gloo.set_clear_color('white')
        gloo.set_state('translucent')

        # config your lines
        gloo.set_line_width(2.0)

        # show the canvas
        self.show()

        self.timer = app.Timer(interval=0.05, connect=self.timer_callback, start=True)

    def calibrate(self):
        poseMatrix = self.tracker.getTrackerData()

        if (poseMatrix != False):
            self.calibrationPosition = np.array([[poseMatrix.m[0][0], poseMatrix.m[0][1], poseMatrix.m[0][2], poseMatrix.m[0][3]],
                             [poseMatrix.m[1][0], poseMatrix.m[1][1], poseMatrix.m[1][2], poseMatrix.m[1][3]],
                             [poseMatrix.m[2][0], poseMatrix.m[2][1], poseMatrix.m[2][2], poseMatrix.m[2][3]]])

        print("Calibrated: ")
        print(self.calibrationPosition)

    def update_position(self):

        #self.tracker.checkForTriggerEvent()
        try:
            az, el, r = self.tracker.getRelativePosition()
        except:
            az = 0
            el = 0
            r = 1

        #self.phi = az
        #self.theta = el

        self.update()

        return

        poseMatrix = self.tracker.getTrackerData()

        if(poseMatrix != False):

            pose = np.array([[poseMatrix.m[0][0], poseMatrix.m[0][1], poseMatrix.m[0][2], poseMatrix.m[0][3]],
                             [poseMatrix.m[1][0], poseMatrix.m[1][1], poseMatrix.m[1][2], poseMatrix.m[1][3]],
                             [poseMatrix.m[2][0], poseMatrix.m[2][1], poseMatrix.m[2][2], poseMatrix.m[2][3]]])

            pose[:, 3] = np.subtract(pose[:, 3], self.calibrationPosition[:, 3])

            self.data2 = np.array([[0, 0, 0],
                           [pose[0][0], pose[1][0], pose[2][0]],
                           [0, 0, 0],
                           [pose[0][1], pose[1][1], pose[2][1]],
                           [0, 0, 0],
                           [pose[0][2], pose[1][2], pose[2][2]]])
            #self.translateXYZ(self.data2, 1)

            self.data2[:, 0] += pose[0][3] * 10
            self.data2[:, 1] += pose[1][3] * 10
            self.data2[:, 2] += pose[2][3] * 10


            self.data2 = self.data2.astype(np.float32)
            #np.append(self.data2, [[0, 0, 0,], [poseMatrix.m[0][1], poseMatrix.m[1][1], poseMatrix.m[2][1]]], axis=0)
        self.update()

    def translateXYZ(self, data, x):
        data[:, 0] += x

    def make_box_lines(self, size):

        s = size / 2
        v1 = np.array([-s, -s, -s])
        v2 = np.array([-s, -s, s])
        v3 = np.array([s, -s, s])
        v4 = np.array([s, -s, -s])
        v5 = np.array([-s, s, -s])
        v6 = np.array([-s, s, s])
        v7 = np.array([s, s, s])
        v8 = np.array([s, s, -s])

        vertices = np.array([[v1], [v2], [v3], [v4], [v5], [v6], [v7], [v8]], dtype=np.float32)

        indices = np.array([0, 1,
                            1, 2,
                            2, 3,
                            3, 0,
                            4, 5,
                            5, 6,
                            6, 7,
                            7, 4,
                            0, 4,
                            3, 7,
                            2, 6,
                            1, 5], dtype=np.uint32)

        return vertices, indices


    def make_plane_grid(self, size, num_grid_lines):
        start = size/2
        delta = size / (num_grid_lines - 1)

        grid_data = np.empty([num_grid_lines*4, 3])
        index = 0
        for i in range(num_grid_lines):
            p1x = -start + i * delta
            p1y = - start
            grid_data[index] = [p1x, 0.0, p1y]
            index += 1

            p2x = p1x
            p2y = start
            grid_data[index] = [p2x, 0, p2y]
            index += 1

        for i in range(num_grid_lines):
            p1x = -start
            p1y = - start + i * delta
            grid_data[index] = [p1x, 0.0, p1y]
            index += 1

            p2x = - p1x
            p2y = p1y
            grid_data[index] = [p2x, 0, p2y]
            index += 1

        return grid_data


    def sphere(self, radius, rings, sectors):

        R = 1 / (rings - 1)
        S = 1 / (sectors - 1)
        r2d = 180 / np.pi
        vertices = np.zeros((rings*sectors, 3))
        i = 0
        for r in range(rings):
            for s in range(sectors):
                phi = np.pi * r * R
                omega = 2 * np.pi * s * S
                print("p", i, "=", omega*r2d, "|", phi*r2d, "  r=", r, "  s=", s)
                vertices[i][1] = -np.sin(-np.pi / 2 + phi) * radius
                vertices[i][2] = np.cos(omega) * np.sin(phi) * radius
                vertices[i][0] = np.sin(omega) * np.sin(phi) * radius

                i += 1

        indices = np.zeros((rings-3)*(sectors-1)*6, dtype=np.uint32)
        numLinesV = (rings - 1) * (sectors - 1)
        numLinesH = (rings - 2) * (sectors - 1)
        line_indices = np.array([])

        i = 0
        for r in range(1, rings - 2):
            for s in range(sectors-1):

                q1 = r * sectors + s
                q2 = r * sectors + (s + 1)
                q3 = (r + 1) * sectors + (s + 1)
                q4 = (r + 1) * sectors + s
                print("s", i, "=", q1, " ", q2, " ",q3, " ",q4)
                indices[i] = q1
                indices[i+1] = q2
                indices[i+2] = q3
                indices[i+3] = q1
                indices[i+4] = q4
                indices[i+5] = q3

                line_indices = np.append(line_indices, [q1, q2, q2, q3, q3, q4, q4, q1])

                i = i +6

        #add triangles around top pole
        for s in range(sectors-1):
            q1 = 0
            q2 = sectors + s
            q3 = q2 + 1
            indices = np.append([q1, q2, q3], indices)
            line_indices = np.append([q1, q2], line_indices)

         # add triangles around bottom pole
        for s in range(sectors - 1):
            q1 = sectors * (rings-1)
            q2 = sectors*(rings-2) + s
            q3 = q2 + 1
            indices = np.append(indices, [q1, q2, q3])
            line_indices = np.append(line_indices, [q1, q2])


        indices = indices.astype(np.uint32)
        line_indices = line_indices.astype(np.uint32)

        # indices = np.array([11, 5, 6,
        #                     5, 10, 11,
        #                     6, 7, 12,
        #                     6, 11, 12,
        #                     7, 8, 13,
        #                     7, 12, 13,
        #                     8, 9, 14,
        #                     0, 5, 6], dtype=np.uint32)






        return vertices, indices, line_indices


    def on_resize(self, event):
        """
        We create a callback function called when the window is being resized.
        Updating the OpenGL viewport lets us ensure that
        Vispy uses the entire canvas.
        """
        gloo.set_viewport(0, 0, *event.physical_size)
        ratio = event.physical_size[0] / float(event.physical_size[1])
        self.program['u_projection'] = perspective(45.0, ratio, 2.0, 10.0)

    def on_draw(self, event):


        #self.tracker.getTrackerData()

        """ refresh canvas """
        gloo.clear()
        view = translate((0, -0.5, -self.z))
        model = np.dot(rotate(self.theta, (0, 1, 0)), rotate(self.phi, (0, 0, 1)))
        self.program['u_model'] = model
        self.program['u_view'] = view
        self.program['a_position'] = self.data
        self.program['a_sourceColour'] = self.data_color
        #self.program.draw('triangles', self.indices)
        self.program.draw('lines', self.line_indices)
        #self.program.draw('lines')


        self.program['a_position'] = self.data2
        self.program['a_sourceColour'] = self.data_color2

        #view = translate((0, 0, -self.z))
        az, el, r = self.tracker.getRelativePosition()
        #print("Az: ", az, "   El: ", el)
        model = np.dot(translate((self.sphereradius + self.boxsize/2, 0, 0)), np.dot(rotate(el-90, (0, 0, 1)), rotate(az, (0, 1, 0))))
        #model = np.dot(rotate(0, (0, 1, 0)), rotate(0, (0, 0, 1)))
        # note the convention is, theta is applied first and then phi
        # see vispy.utils.transforms,
        # python is row-major and opengl is column major,
        # so the rotate function transposes the output.
        self.program['u_model'] = model
        self.program['u_view'] = view
        self.program.draw('lines', self.indices2)

        self.program['a_position'] = self.data3
        self.program['a_sourceColour'] = self.data_color3
        self.program.draw('lines')


    def update_angle(self, theta, phi):
        self.theta = theta
        self.phi = phi

    def update_phi(self, phi):
        self.phi = phi * 3.6
        #print("Phi: ", self.phi, "  Theta: ", self.theta)
        self.update()

    def update_theta(self, theta):
        self.theta = theta * 3.6
        #print("Phi: ", self.phi, "  Theta: ", self.theta)

        self.update()

    def inc_angle(self):
        self.theta = self.theta + 10
        self.update()
        print("Inc Angle")

    def timer_callback(self, event):
        #self.theta = self.theta + 1
        self.update_position()


    def start(self):

        app.run()

