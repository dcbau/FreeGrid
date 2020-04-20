import sys
import numpy as np

from vispy import app, gloo, geometry, visuals
from vispy.util.transforms import perspective, translate, rotate
from vispy.geometry.generation import create_sphere
from vispy.color.colormap import get_colormaps

from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import pywavefront

import tracker_manager
from GUI.gl_shapes import Sphere, Speaker

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
    gl_PointSize = 10.0;
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

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.color = QColor(0, 0, 0)

    def paintEvent(self, event):
        pass

    def mousePressEvent(self, event):
        self.clicked.emit()


class TrackerOrientation():
    def __init__(self, tracker_ref):
        self.tracker = tracker_ref

        self.colors = np.array([[1.0, 0.0, 0.0, 1.0],
                                [1.0, 0.0, 0.0, 1.0],
                                [0.0, 1.0, 0.0, 1.0],
                                [0.0, 1.0, 0.0, 1.0],
                                [0.0, 0.0, 1.0, 1.0],
                                [0.0, 0.0, 1.0, 1.0]], dtype=np.float32)

    def draw(self, program):

        try:
            pose1, pose2 = self.tracker.getTrackerData()
            #r = self.tracker.getDirectionVector()

        except:
            return

        transvec = np.array([pose2.m[0][3] - pose1.m[0][3],
                             pose2.m[1][3] - pose1.m[1][3],
                             pose2.m[2][3] - pose1.m[2][3]])

        #r = transvec

        #r = r / np.linalg.norm(r)
        #r = r * 1.5


        # tracker 1 (place at origin)
        origin = np.array([0.0, 0.0, 0.0])
        x_axis = np.array([pose1.m[0][2], pose1.m[1][2], pose1.m[2][2]])
        y_axis = np.array([pose1.m[0][1], pose1.m[1][1], pose1.m[2][1]])
        z_axis = np.array([pose1.m[0][0], pose1.m[1][0], pose1.m[2][0]])

        vertices_1 = np.array([origin, x_axis,
                               origin, y_axis,
                               origin, z_axis], dtype=np.float32)


        # tracker 2 (relative to tracker 1)

        x_axis = transvec + np.array([pose2.m[0][2], pose2.m[1][2], pose2.m[2][2]])
        y_axis = transvec + np.array([pose2.m[0][1], pose2.m[1][1], pose2.m[2][1]])
        z_axis = transvec + np.array([pose2.m[0][0], pose2.m[1][0], pose2.m[2][0]])

        vertices_2 = np.array([transvec, x_axis,
                               transvec, y_axis,
                               transvec, z_axis], dtype=np.float32)




        program['a_position'] = vertices_1
        program['a_sourceColour'] = self.colors
        program['u_model'] = np.identity(4)
        program.draw('lines')

        program['a_position'] = vertices_2
        program['a_sourceColour'] = self.colors
        program['u_model'] = np.identity(4)
        program.draw('lines')


class AzimuthAngleDisplay():
    def __init__(self, radius=1):

        self.steps = 360
        num_vertices = self.steps + 1
        # radius = 1
        self.az = np.linspace(0, 2 * np.pi, self.steps)
        x = np.sin(self.az) * radius
        y = 0 * self.az
        z = -np.cos(self.az) * radius

        vertices = np.array([x.flatten(), y.flatten(), z.flatten()]).transpose()
        origin = np.array([[0, 0, 0]])
        vertices = np.append(origin, vertices, axis=0)
        self.vertices = np.ascontiguousarray(vertices, dtype=np.float32)

        # colors ##########################

        num_vertices, num_coords = vertices.shape
        color = np.array([0.0, 0.3, 0.0, 0.2])
        pixel_colors = np.tile(color, (num_vertices, 1))

        self.colors = pixel_colors.astype(np.float32)

    def draw(self, program, azimuth):

        indices = np.array([])
        for i in range(1, self.steps):
            current_az = self.az[i] * 180 / np.pi
            if current_az > azimuth:
                break

            p1 = 0
            p2 = i
            p3 = i + 1

            indices = np.append(indices, [(p1, p2, p3)])

        indices = gloo.IndexBuffer(indices.astype(np.uint32))

        program['u_model'] = np.identity(4)

        program['a_position'] = self.vertices
        program['a_sourceColour'] = self.colors
        program.draw('triangle_strip', indices=indices)

class DrawVector():
    def __init__(self, radius = 1, alpha=1.0):
        self.alpha = alpha
        pass
    def draw(self, program, x1, y1, z1, x2=0.0, y2=0.0, z2=0.0, x3=0.0, y3=0.0, z3=0.0):

        vertices = np.array([[0.0, 0.0, 0.0],
                             [x1, y1, z1],
                             [0.0, 0.0, 0.0],
                             [x2, y2, z2],
                             [0.0, 0.0, 0.0],
                             [x3, y3, z3]])

        #print(x3, y3, z3)

        vertices = np.ascontiguousarray(vertices, dtype=np.float32)

        colors = np.array([[1.0, 0.0, 0.0, self.alpha],
                           [1.0, 0.0, 0.0, self.alpha],
                           [0.0, 1.0, 0.0, self.alpha],
                           [0.0, 1.0, 0.0, self.alpha],
                           [0.0, 0.0, 1.0, self.alpha],
                           [0.0, 0.0, 1.0, self.alpha]]).astype(np.float32)

        program['u_model'] = np.identity(4)

        program['a_position'] = vertices

        program['a_sourceColour'] = colors
        program.draw('lines')


class ElevationAngleDisplay():
    def __init__(self, radius=1):

        self.steps = 180
        num_vertices = self.steps + 1
        self.el = np.linspace(0, np.pi / 2, self.steps)
        x = 0 * self.el
        y = np.sin(self.el) * radius
        z = -np.cos(self.el) * radius

        vertices = np.array([x.flatten(), y.flatten(), z.flatten()]).transpose()
        origin = np.array([[0, 0, 0]])
        vertices = np.append(origin, vertices, axis=0)
        self.vertices_pos = np.ascontiguousarray(vertices, dtype=np.float32)

        vertices[:, 1] *= -1
        self.vertices_neg = np.ascontiguousarray(vertices, dtype=np.float32)
        # colors ##########################

        num_vertices, num_coords = vertices.shape
        color = np.array([0.3, 0.0, 0.0, 0.2])
        pixel_colors = np.tile(color, (num_vertices, 1))

        self.colors = pixel_colors.astype(np.float32)

    def draw(self, program, azimuth, elevation):

        indices = np.array([])
        for i in range(1, self.steps):
            current_el = self.el[i] * 180 / np.pi
            if current_el > np.abs(elevation):
                break

            p1 = 0
            p2 = i
            p3 = i + 1

            indices = np.append(indices, [(p1, p2, p3)])

        indices = gloo.IndexBuffer(indices.astype(np.uint32))

        program['u_model'] = rotate(azimuth, (0, -1, 0))

        if elevation > 0:
            program['a_position'] = self.vertices_pos
        else:
            program['a_position'] = self.vertices_neg

        program['a_sourceColour'] = self.colors
        program.draw('triangle_strip', indices=indices)

class SpherePoints():
    def __init__(self, radius=1):
        self.point_angles = []
        self.vertices = []
        self.colors = []
        self.radius = radius

    def add_point(self, az, el):

        print("Point: ", az, "  ", el)
        self.point_angles.append([az, 90 - el])

        num_vertices = int(len(self.point_angles))
        self.vertices = np.zeros([num_vertices, 3], dtype=np.float32)
        self.colors = np.zeros([num_vertices, 4], dtype=np.float32)

        r = self.radius
        for i in range(num_vertices):
            az = (self.point_angles[i][0] - 90) * np.pi / 180.0
            el = self.point_angles[i][1] * np.pi / 180.0
            self.vertices[i][0] = r * np.sin(el) * np.cos(az)
            self.vertices[i][1] = r * np.cos(el)
            self.vertices[i][2] = r * np.sin(el) * np.sin(az)

            self.colors[i][0] = 1.0
            self.colors[i][1] = 0.0
            self.colors[i][2] = 0.0
            self.colors[i][3] = 1.0

    def draw(self, program):

        if len(self.vertices) == 0:
            return

        program['u_model'] = np.identity(4)

        program['a_position'] = self.vertices
        program['a_sourceColour'] = self.colors
        program.draw('points')


class VispyCanvas(app.Canvas):

    def __init__(self, theta=0, phi=45, z=6.0):

        self.calibrationPosition = np.empty([3, 4])

        self.tracker = tracker_manager.TrackerManager()

        app.Canvas.__init__(self, size=(200, 200), title='plot3d',
                            keys='interactive')
        # app.use_app('PyQt5')

        N = 1000
        self.data = np.c_[
            np.sin(np.linspace(-10, 10, N) * np.pi),
            np.cos(np.linspace(-10, 10, N) * np.pi),
            np.linspace(-2, 2, N)]

        # self.data = self.make_plane_grid(5, 9)
        self.sphereradius = 1.5
        self.boxsize = 0.4
        # self.data, self.indices, self.line_indices = self.sphere(self.sphereradius, 15, 20)

        self.sphere = Sphere(self.sphereradius, 15, 20)

        self.speaker = Speaker(self.boxsize)

        # testangles = np.array([[0, 90],
        #                       [90, 90],
        #                       [180, 90],
        #                       [270, 90]])

        self.meas_points = SpherePoints(self.sphereradius)
        # for row in testangles:
        #    self.meas_points.add_point(row[0], row[1])

        self.tracker_orientation = TrackerOrientation(self.tracker)
        self.azimuthdisplay = AzimuthAngleDisplay(self.sphereradius)
        self.elevationdisplay = ElevationAngleDisplay(self.sphereradius)

        # scene = pywavefront.Wavefront('resources/untitled.obj')

        program = gloo.Program(vert=vertex, frag=fragment)
        # program.bind(self.data2)

        # initialize 3D view
        view = np.eye(4, dtype=np.float32)
        model = np.eye(4, dtype=np.float32)
        projection = np.eye(4, dtype=np.float32)

        # update program
        program['u_model'] = model
        program['u_view'] = view
        program['u_projection'] = projection
        # program['a_position'] = gloo.VertexBuffer(self.data)

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

    def update_position(self):

        # self.tracker.checkForTriggerEvent()
        try:
            az, el, r = self.tracker.getRelativePosition()
        except:
            az = 90
            el = 0
            r = 1

        # self.phi = az
        # self.theta = el

        self.update()

        return

        poseMatrix = self.tracker.getTrackerData()

        if (poseMatrix != False):
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
            # self.translateXYZ(self.data2, 1)

            self.data2[:, 0] += pose[0][3] * 10
            self.data2[:, 1] += pose[1][3] * 10
            self.data2[:, 2] += pose[2][3] * 10

            self.data2 = self.data2.astype(np.float32)
            # np.append(self.data2, [[0, 0, 0,], [poseMatrix.m[0][1], poseMatrix.m[1][1], poseMatrix.m[2][1]]], axis=0)
        self.update()

    def translateXYZ(self, data, x):
        data[:, 0] += x

    def make_plane_grid(self, size, num_grid_lines):
        start = size / 2
        delta = size / (num_grid_lines - 1)

        grid_data = np.empty([num_grid_lines * 4, 3])
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

        # self.tracker.getTrackerData()

        """ refresh canvas """
        gloo.clear()

        view = np.dot(np.dot(rotate(self.theta, (0, 1, 0)), rotate(self.phi, (1, 0, 0))), translate((0, -0.5, -self.z)))
        self.program['u_view'] = view

        self.sphere.draw(self.program)

        az, el, r = self.tracker.getRelativePosition()
        self.speaker.draw(self.program, az, el, self.sphereradius)

        self.meas_points.draw(self.program)

        #self.tracker_orientation.draw(self.program)


        self.azimuthdisplay.draw(self.program, az)
        self.elevationdisplay.draw(self.program, az, el)

        # oriantation1 = DrawVector(alpha=1)
        # oriantation2 = DrawVector(alpha=1)
        #
        #
        # #print(viewVec)
        # try:
        #     vec1_x, vec1_y, vec1_z, vec2_x, vec2_y, vec2_z = self.tracker.getViewVector()
        #     oriantation1.draw(self.program, vec1_x[0], vec1_x[1], vec1_x[2],
        #                                     vec1_y[0], vec1_y[1], vec1_y[2],
        #                                     vec1_z[0], vec1_z[1], vec1_z[2])
        #     #oriantation2.draw(self.program, vec2_x[0], vec2_x[1], vec2_x[2],
        #     #                                vec2_y[0], vec2_y[1], vec2_y[2],
        #     #                                vec2_z[0], vec2_z[1], vec2_z[2])
        # except:
        #     pass


    def update_angle(self, theta, phi):
        self.theta = theta
        self.phi = phi

    def update_phi(self, phi):
        self.phi = -phi * 3.6
        # print("Phi: ", self.phi, "  Theta: ", self.theta)
        self.update()

    def update_theta(self, theta):
        self.theta = theta * 3.6
        # print("Phi: ", self.phi, "  Theta: ", self.theta)

        self.update()

    def inc_angle(self):
        self.theta = self.theta + 10
        self.update()
        print("Inc Angle")

    def timer_callback(self, event):
        # self.theta = self.theta + 1
        self.update_position()

    def start(self):

        app.run()
