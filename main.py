import matplotlib.pyplot as plt
from matplotlib import cm
from grid_filling import *
import tracker_manager

import time
from PyQt5 import QtWidgets
import sys

from GUI.gui_main import gui_main
from measurement import Measurement
def plotPoints(_az, _el, plotRadius, color, plot):
    xyz = sph2cart(_az, _el, plotRadius)
    plot.scatter(xyz[0], xyz[1], xyz[2], c=color, linewidth=2)


def plotSphere(radius, plot):
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)

    x = 10 * np.outer(np.cos(u), np.sin(v))
    y = 10 * np.outer(np.sin(u), np.sin(v))
    z = 10 * np.outer(np.ones(np.size(u)), np.cos(v))

    plot.plot_surface(x, y, z, cmap='Greys', alpha=0.5)

# def getDistancesInverseMapping(p_az, p_el, grid_az, grid_el):
#
#     y1 = p_az
#     x1 = p_el
#
#     y2 = grid_az
#     x2 = grid_el
#
#     # make the single point value a matrix with same dimensions than the grid
#     x1 = x1 * np.ones_like(x2)
#     y1 = y1 * np.ones_like(y2)
#
#     distances = np.power(y2 - y1, 2) + np.power(x2 - x1, 2);
#
#     return distances



def makeGrid(numsamples):
    aaz = np.linspace(0, 1, 6)
    ael = np.linspace(0, 1, 6)

    aaz = aaz * 360.0
    ael = np.arccos(2 * ael - 1) * 180 / np.pi

    size = aaz.size * ael.size
    grid = np.zeros(size * 2)
    grid.shape = (size, 2)


    i = 0
    for e in ael:
        for a in aaz:
            grid[i, 0] = a
            grid[i, 1] = e
            i += 1

    #grid = np.hstack((aaz, ael))

    return grid


def demo_adding_samplepoints():

    # create a random grid with gaps
    input_grid = makeRandomGridFromGauss(16, 3, 5)

    # create a grid with the points to be considered as candidates for filling
    correctionGrid_10_10 = makeGaussGrid(10, 10)


    # calculate condition value as a reference
    SHOrder = np.floor(np.sqrt((np.size(input_grid, 0))) - 2)
    Ynm = get_sph_harms(SHOrder, input_grid[:, 0], input_grid[:, 1])
    print("Condition without improving on SH Order ", SHOrder, ": ", np.linalg.cond(Ynm))


    #make correction grid
    corr_points = addSamplepoints(input_grid, 3, True, correctionGrid_10_10, None)
    corr_points1 = addSamplepoints(input_grid, 3, True, correctionGrid_10_10, 1)
    corr_points2 = addSamplepoints(input_grid, 3, True, correctionGrid_10_10, 2)
    corr_points3 = addSamplepoints(input_grid, 3, True, correctionGrid_10_10, 3)

    print("Points with Adaptive Order: ", corr_points)
    print("Points with Order 1: ", corr_points1)
    print("Points with Order 2: ", corr_points2)
    print("Points with Order 3: ", corr_points3)



    fig = plt.figure()
    # ax = plt.axes(projection='3d')
    ax = fig.add_subplot(1, 2, 1, projection='3d')

    plotSphere(9.5, ax)
    plotPoints(input_grid[:, 0], input_grid[:, 1], 10, 'k', ax)
    plotPoints(corr_points[:, 0], corr_points[:, 1], 10, 'r', ax)
    plotPoints(corr_points1[:, 0], corr_points1[:, 1], 10, 'g', ax)
    plotPoints(corr_points3[:, 0], corr_points3[:, 1], 10, 'b', ax)

    ax = fig.add_subplot(1, 2, 2)

    ax.set_xlim([0, 360])
    ax.set_ylim([0, 180])
    ax.scatter(input_grid[:, 0], 180-input_grid[:, 1], color='k', linewidths=3)
    ax.scatter(corr_points[:, 0], 180-corr_points[:, 1], color='r', linewidths=3)
    ax.scatter(corr_points1[:, 0], 180-corr_points1[:, 1], color='g', linewidths=3)
    ax.scatter(corr_points3[:, 0], 180-corr_points3[:, 1], color='b', linewidths=3)



    plt.show()

def main():


    #demo_adding_samplepoints()

    app = QtWidgets.QApplication(sys.argv)

    measurement = Measurement()

    main = gui_main(measurement)
    main.show()
    #main._ui.vispy_canvas.show()

    #main._ui.vispy_canvas.start()

    sys.exit(app.exec_())



def mainOld():


    # myGrid = makeRandomGridFromGaussian(10, 3, 10)
    myGrid = makeRandomGrid(10)
    print(myGrid)

    # myGrid = makeEquiangularGridByOrder(4)

    # xyz = sph2cart(myGrid[:,0], myGrid[:,1], 10.5)
    #
    # ax = plt.axes(projection='3d')
    #
    # plotSphere(10, ax)
    # ax.scatter(xyz[0], xyz[1], xyz[2], 'k', linewidth=2)
    # plt.show()

    t0 = time.time()

    A, E, NN = calculateDensityAreas(myGrid, 200)

    t1 = time.time()

    print("Time elapsed: ", t1 - t0)

    fmax, fmin = NN.max(), NN.min()
    NN = (NN - fmin) / (fmax - fmin)

    az = np.array([0, 90, 180, 270])
    el = np.array([90, 90, 90, 90])

    az = myGrid[:, 0] * np.size(NN, 0) / 360
    el = myGrid[:, 1] * np.size(NN, 1) / 180
    values = angularDistance(350, 90, 10, 90)

    # make a good color mapping
    avg = np.average(NN)
    NN = np.where(NN < avg + 0.2, -1, NN)
    # print(values)

    fig = plt.figure()

    # ax = plt.axes(projection='3d')
    ax = fig.add_subplot(1, 2, 1, projection='3d')

    x, y, z = sph2cart(A, E, 10)
    ax.plot_surface(x, y, z, facecolors=cm.Reds(NN))

    xyz = sph2cart(myGrid[:, 0], myGrid[:, 1], 10.5)
    ax.scatter(xyz[0], xyz[1], xyz[2], 'k', linewidth=2)

    # plotSphere(10, ax)
    # plotPoints(az, el, 10, 'b', ax)
    # plotPoints(myGrid[:,0], myGrid[:,1], 10.5, 'g', ax)

    myGrid[0] = myGrid[0] / 360
    myGrid[1] = myGrid[1] / 180

    ax = fig.add_subplot(1, 2, 2)
    ax.scatter(az, el, color='k', linewidths=3)
    ax.imshow(NN, cmap='Reds', interpolation='nearest')

    plt.show()

    Az1 = 90
    El1 = 50
    Az2 = 100
    El2 = 50



if __name__ == '__main__':
    main()
