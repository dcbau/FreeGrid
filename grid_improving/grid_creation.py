import numpy as np


def makeGaussGridByOrder(order):

    nAz = 2*(order + 1)
    nEl = order + 1

    return makeGaussGrid(nAz, nEl + 2)


def makeGaussGrid(resolutionAz, resolutionEl):

    az = np.linspace(0, 360, resolutionAz + 1)
    el = np.linspace(0, 180, resolutionEl)

    # remove last element of azimuth list to avoid 0°/360° ambiguity
    az = np.delete(az, resolutionAz)
    # remove 0° and 180° from elevation list  to avoid multiple north/south poles
    el = np.delete(el, [0, resolutionEl - 1])


    size = az.size  * el.size + 2
    grid = np.zeros(size * 2)
    grid.shape = (size, 2)

    #add northpole
    grid[0, 0] = 0.0
    grid[0, 1] = 0.0

    i = 1
    for e in el:
        for a in az:
            grid[i, 0] = a
            grid[i, 1] = e
            i += 1

    #add soutpole
    grid[size-1, 0] = 0.0
    grid[size-1, 1] = 180.0

    print("Npoints: ", np.size(grid, 0))

    return grid

def makeRandomGridFromGauss(numSamplePoints, baseGridOrder, variance):

    # make a regular grid
    regularGrid = makeGaussGridByOrder(baseGridOrder)

    # randomly select points from it
    idx = np.arange(np.size(regularGrid, 0))
    idx = np.random.permutation(idx)
    idx = idx[0:numSamplePoints]
    randomGrid = regularGrid[idx, :]

    # apply random angular variance
    varianceAz = (np.random.rand(np.size(randomGrid, 0)) - 0.5) * 2 * variance
    varianceEl = (np.random.rand(np.size(randomGrid, 0)) - 0.5) * 2 * variance
    randomGrid[:, 0] = (randomGrid[:, 0] + varianceAz) % 360
    randomGrid[:, 1] = (randomGrid[:, 1] + varianceEl) % 180


    return randomGrid

def makeRandomGrid(numSamplePoints):

    #distribution taken from http://mathworld.wolfram.com/SpherePointPicking.html

    az = np.random.rand(numSamplePoints, 1) * 360.0
    el = np.arccos(2 * np.random.rand(numSamplePoints, 1) - 1) * 180 / np.pi

    grid = np.hstack((az, el))

    return grid