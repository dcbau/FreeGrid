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



        self.sphereradius = 1.5
        self.boxsize = 0.4

        self.sphere = Sphere(self.sphereradius, 15, 20)
        self.speaker = Speaker(self.boxsize)

        self.meas_points = SpherePoints(self.sphereradius)

        #self.tracker_orientation = TrackerOrientation(self.tracker)
        self.azimuthdisplay = AzimuthAngleDisplay(self.sphereradius)
        self.elevationdisplay = ElevationAngleDisplay(self.sphereradius)

        program = gloo.Program(vert=vertex, frag=fragment)

        # initialize 3D view
        view = np.eye(4, dtype=np.float32)
        model = np.eye(4, dtype=np.float32)
        projection = np.eye(4, dtype=np.float32)

        # update program
        program['u_model'] = model
        program['u_view'] = view
        program['u_projection'] = projection
        # program['a_position'] = gloo.VertexBuffer(self.data)

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

        """ refresh canvas """
        gloo.clear()

        view = np.dot(np.dot(rotate(self.theta, (0, 1, 0)), rotate(self.phi, (1, 0, 0))), translate((0, -0.5, -self.z)))
        self.program['u_view'] = view

        self.sphere.draw(self.program)

        az, el, r = self.tracker.getRelativePosition()
        self.speaker.draw(self.program, az, el, self.sphereradius)

        self.meas_points.draw(self.program)

        self.azimuthdisplay.draw(self.program, az)
        self.elevationdisplay.draw(self.program, az, el)

    def update_phi(self, phi):
        self.phi = -phi * 3.6
        self.update()

    def update_theta(self, theta):
        self.theta = theta * 3.6
        self.update()

    def timer_callback(self, event):
        self.update()


    def start(self):
        app.run()
