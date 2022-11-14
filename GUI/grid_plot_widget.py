from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time


matplotlib.rcParams.update({'axes.titlesize': 8})
matplotlib.rcParams.update({'axes.labelsize': 7})
matplotlib.rcParams.update({'xtick.labelsize': 7})
matplotlib.rcParams.update({'ytick.labelsize': 7})
matplotlib.rcParams.update({'axes.titleweight': 'bold'})

class GridPlotWidget(QtWidgets.QWidget):

    def __init__(self, controller_ref, *args, **kwargs):
        super(GridPlotWidget, self).__init__(*args, **kwargs)

        self.controller_ref = controller_ref

        self.plot_color = 'xkcd:teal'

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.plot = plt.figure()
        self.plot.set_facecolor("none")
        self.plot_canvas = FigureCanvas(self.plot)
        self.plot_canvas.setStyleSheet("background-color:transparent;")
        self.layout().addWidget(self.plot_canvas)

        #self.activateMarkerButton = QtWidgets.QCheckBox("Show Current Position")
        #self.activateMarkerButton.setChecked(True)
        #self.activateMarkerButton.clicked.connect(self.activateMarkerButton_clicked)
        #self.layout().addWidget(self.activateMarkerButton)

        self.redraw_points = False
        self.redraw_recommend_points = False
        self.redraw_highlight_point = None

        fig = self.plot.gca()
        self.points_plot = fig.plot([], [], '.', color=self.plot_color, markersize=8)
        self.recom_points_plot = fig.plot([], [], '*', color='xkcd:gold', markersize=10)
        self.draw_marker = fig.plot(0, 0, '+', color='black', markersize=13)

        self.hl_point_plot = fig.plot([], [], 'o', markerfacecolor='none', markeredgecolor='xkcd:red', markersize=10)

        self.recom_points = np.empty((0, 2))
        self.points = np.empty((0, 2))

        fig.set_title("Measurement Grid")
        fig.set_xlim([-185, 185])
        fig.set_xticks([-180, -90, 0, 90, 180])
        fig.set_xticklabels(['180', '270', '0', '90', '180'])
        fig.set_ylim([-95, 95])
        fig.set_yticks([-90, -45, 0, 45, 90])
        fig.set_ylabel('Elevation')
        fig.set_xlabel('Azimuth')
        fig.grid(linestyle='--', alpha=0.5, linewidth=0.5)

        self.ani = animation.FuncAnimation(self.plot, self.update_graphics, interval=200, blit=True)

    #
    # def activateMarkerButton_clicked(self, value):
    #     if value:
    #         self.ani.resume()
    #         self.draw_marker[0].set_marker(matplotlib.markers.MarkerStyle('x'))
    #         #self.ani = animation.FuncAnimation(self.plot1, self.update_marker, interval=50, init_func=self.init_marker)
    #     else:
    #         #self.update_marker()
    #
    #         self.draw_marker[0].set_marker(matplotlib.markers.MarkerStyle(None))
    #         self.draw_marker[0].set_xdata(0)
    #
    #         self.ani.pause()

    def getAngles(self):
        az, el, r = self.controller_ref.get_tracking_angles()
        if az > 180:
            az = az - 360
        return az, el

    def update_graphics(self, *args):

        update_artists = []

        # update grid points
        self.points_plot[0].set_xdata(self.points[:, 0])
        self.points_plot[0].set_ydata(self.points[:, 1])
        update_artists.append(self.points_plot[0])

        # update recommender points
        self.recom_points_plot[0].set_xdata(self.recom_points[:, 0])
        self.recom_points_plot[0].set_ydata(self.recom_points[:, 1])
        update_artists.append(self.recom_points_plot[0])

        # update highlighted points
        if self.redraw_highlight_point is not None:
            try:
                self.hl_point_plot[0].set_xdata(self.points[self.redraw_highlight_point, 0])
                self.hl_point_plot[0].set_ydata(self.points[self.redraw_highlight_point, 1])
            except IndexError:
                self.redraw_highlight_point = None
            update_artists.append(self.hl_point_plot[0])

        # update current head position marker
        az, el = self.getAngles()
        self.draw_marker[0].set_xdata(az)
        self.draw_marker[0].set_ydata(el)
        update_artists.append(self.draw_marker[0])




        update_artists.reverse()
        return update_artists

    def plot_points(self):
        self.redraw_points = True
        return

        self.points_plot[0].set_xdata(self.points[:, 0])
        self.points_plot[0].set_ydata(self.points[:, 1])
        self.recom_points_plot[0].set_xdata(self.recom_points[:, 0])
        self.recom_points_plot[0].set_ydata(self.recom_points[:, 1])

    def add_point(self, az, el):
        if az > 180:
            az = az - 360
        self.points = np.append(self.points, np.array([[az, el]]), axis=0)

    def add_recommendation_point(self, az, el):
        if az > 180:
            az = az - 360
        self.recom_points = np.append(self.recom_points, np.array([[az, el]]), axis=0)

    def highlight_point(self, idx):
        """ If idx==None, no point will be highlighted"""
        self.redraw_highlight_point = idx




    def clear_recommendation_points(self, idx=None):
        """ If idx is None (default), all recommendation points will be cleared"""
        if idx is None:
            self.recom_points = np.empty((0, 2))
        else:
            try:
                self.recom_points = np.delete(self.recom_points, idx, axis=0)
            except IndexError:
                print("Could not delete point: Invalid id")

        self.redraw_recommend_points = True

    def clear_points(self, idx=None):
        """ If idx is None (default), all points will be cleared"""
        if idx is None:
            self.points = np.empty((0, 2))
        else:
            try:
                self.points = np.delete(self.points, idx, axis=0)
            except IndexError:
                print("Could not delete point: Invalid id")

        self.highlight_point(None)
        self.redraw_points = True
