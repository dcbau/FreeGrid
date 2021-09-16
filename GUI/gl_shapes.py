import numpy as np

from vispy import gloo
from vispy.util.transforms import perspective, translate, rotate

class Sphere():
    def __init__(self, radius, rings, sectors):

        # vertex points ##########################

        # create the raw vertex points with a simple meshgrid
        r = np.linspace(0, np.pi, rings)
        s = np.linspace(0, 2*np.pi, sectors)

        sv, rv = np.meshgrid(s, r)

        x = np.sin(sv) * np.sin(rv) * radius
        y = -np.sin(-np.pi/2 + rv) * radius
        z = np.cos(sv) * np.sin(rv) * radius

        vertices = np.array([x.flatten(), y.flatten(), z.flatten()]).transpose()
        self.vertices = np.ascontiguousarray(vertices, dtype=np.float32)

        #    indexing of the spherical array

        #            0   1   2       s-1
        #         0 *---*---* . . .-*
        #           |   |   |       |
        #         s *---*---* . . .-*
        #           |   |   |       |
        #        2s *---*---* . . .-*
        #           :   :   :       :
        #           :   :   :       :
        #   (r-1)*s *---*---* . . .-*
        #
        #               | | |
        #               V V V
        #             |
        #           p1|     |p2
        #           --*-----*----
        #             | \   |
        #             |   \ |
        #         ----*-----*--
        #           p4|     |p3
        #                   |


        # indices ##########################


        indices = np.array([])
        line_indices = np.array([])

        # loop over every quad in the grid except the ones directly around the poles (first and last row)
        for r in range(1, rings - 2):
            for s in range(sectors - 1):

                p1 = r * sectors + s
                p2 = r * sectors + (s + 1)
                p3 = (r + 1) * sectors + (s + 1)
                p4 = (r + 1) * sectors + s

                # make two triangles
                indices = np.append(indices, [(p1, p2, p3), (p1, p4, p3)])

                # make 4 lines
                line_indices = np.append(line_indices, [(p1, p2), (p2, p3), (p3, p4), (p4, p1)])


        # add poles
        for s in range(sectors - 1):

            # top pole
            p1 = 0
            p2 = sectors + s
            p3 = p2 + 1
            indices = np.append([p1, p2, p3], indices)
            line_indices = np.append([p1, p2], line_indices)

            # bottom pole
            p1 = sectors * (rings - 1)
            p2 = sectors * (rings - 2) + s
            p3 = p2 + 1
            indices = np.append(indices, [p1, p2, p3])
            line_indices = np.append(line_indices, [p1, p2])

        self.indices = gloo.IndexBuffer(indices.astype(np.uint32))
        self.line_indices = gloo.IndexBuffer(line_indices.astype(np.uint32))


        # colors ##########################

        num_vertices, num_coords = vertices.shape
        color = np.array([0.0, 0.0, 0.0, 0.3])
        pixel_colors = np.tile(color, (num_vertices, 1))

        self.colors = pixel_colors.astype(np.float32)

    def draw(self, program):

        program['u_model'] = np.identity(4)
        program['a_position'] = self.vertices
        program['a_sourceColour'] = self.colors
        # self.program.draw('triangles', self.indices)
        program.draw('lines', self.line_indices)
        # self.program.draw('lines')

class Speaker():
    def __init__(self, size):
        self.size = size

        s = size / 2
        v1 = np.array([-s, -s, -s])
        v2 = np.array([-s, -s, s])
        v3 = np.array([s, -s, s])
        v4 = np.array([s, -s, -s])
        v5 = np.array([-s, s, -s])
        v6 = np.array([-s, s, s])
        v7 = np.array([s, s, s])
        v8 = np.array([s, s, -s])

        self.vertices = np.array([[v1], [v2], [v3], [v4], [v5], [v6], [v7], [v8]], dtype=np.float32)

        self.indices = np.array([0, 1,
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

        self.indices = gloo.IndexBuffer(self.indices)

        num_vertices = int(self.vertices.size / 3)
        color = np.array([0.0, 0.0, 0.0, 1.0])
        pixel_colors = np.tile(color, (num_vertices, 1))

        self.colors = pixel_colors.astype(np.float32)

    def draw(self, program, az, el, r):

        program['a_position'] = self.vertices
        program['a_sourceColour'] = self.colors

        model = np.dot(translate((0, 0, -(r + self.size / 2))),    np.dot(rotate(el, (1, 0, 0)), rotate(az, (0, 1, 0))))

        program['u_model'] = model
        program.draw('lines', self.indices)

        #reset model transformation
        program['u_model'] = np.identity(4)

