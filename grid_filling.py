import numpy as np
from scipy import special as sp
from grid_creation import *
import itertools
import time

def sph2cart(_az, _el, ra):
    a = _az * np.pi / 180
    e = _el * np.pi / 180

    x = ra * np.multiply(np.cos(a), np.sin(e))
    y = ra * np.multiply(np.sin(a), np.sin(e))
    z = ra * np.cos(e)

    # array = np.array([x, y, z])
    # array = np.round(array * 1000) / 1000

    return x, y, z

def getDistances(p_az, p_el, grid_az, grid_el):
    x1, y1, z1 = sph2cart(p_az, p_el, 1);
    x2, y2, z2 = sph2cart(grid_az, grid_el, 1);

    # make the single point value a matrix with same dimensions than the grid
    x1 = x1 * np.ones_like(x2)
    y1 = y1 * np.ones_like(z2)
    z1 = z1 * np.ones_like(z2)

    dotProduct = np.einsum('ji,ji->i', [x1, y1, z1], [x2, y2, z2])

    distances = np.arccos(np.clip(dotProduct, -1.0, 1.0)) / np.pi;

    return distances

def angularDistance(az1, el1, az2, el2):
    # el1 = el1 - 90;
    # el2 = el2 - 90;

    x1, y1, z1 = sph2cart(az1, el1, 1);
    x2, y2, z2 = sph2cart(az2, el2, 1);

    # distance = np.arctan2(np.linalg.norm(np.cross(xyz1, xyz2)), np.dot(xyz1, xyz2)) / 180;
    distance = np.arccos(np.clip(np.dot([x1, y1, z1], [x2, y2, z2]), -1.0, 1.0)) / np.pi;
    # distance = np.arccos(np.clip(0.5, -1.0, 1.0)) / np.pi;

    return distance


def get_sph_harms(SHOrder, az, el):

    i = 0
    Nsh = (SHOrder + 1) * (SHOrder + 1)
    SH = np.zeros((int(Nsh), np.size(az, 0)), dtype=complex)

    for N in range(int(SHOrder + 1)):
        for M in range(-N, N + 1):
            SH[i] = sp.sph_harm(M, N, az, el)
            i += 1

    return  SH.transpose()


def sph_harm_all(nMax, az, el, m, n):
    #m, n = mnArrays(nMax)
    mA, azA = np.meshgrid(m, az)
    nA, elA = np.meshgrid(n, el)
    return sp.sph_harm(mA, nA, azA, elA)


def mnArrays(SHOrder):

    i = 0
    Nsh = (SHOrder + 1) * (SHOrder + 1)
    n = np.zeros((int(Nsh)))
    m = np.zeros((int(Nsh)))
    for N in range(int(SHOrder + 1)):
        for M in range(-N, N + 1):
            n[i] = N
            m[i] = M
            i += 1

    #print(m)
    #print(n)
    return m, n


def calculateDensityAreas(inputGrid, resolution):
    n = np.size(inputGrid, 0)
    # densityGrid = makeEquiangularGridByOrder(resolution / 2 - 1)

    Az = np.linspace(0, 360, resolution)
    El = np.linspace(0, 180, resolution)
    Az, El = np.meshgrid(Az, El)

    # nGrid = np.size(densityGrid, 0)

    nearestNeighbors = np.zeros_like(Az)

    for i in np.ndindex(np.size(Az, 0), np.size(Az, 1)):
        # minDist = 1
        #
        # for row in inputGrid:
        #     d = angularDistance(row[0], row[1], Az[i], El[i])
        #     #d = row[0] - Az[i]
        #     if d < minDist:
        #         minDist = d
        # nearestNeighbors[i] = minDist

        ds = getDistances(Az[i], El[i], inputGrid[:, 0], inputGrid[:, 1])
        nearestNeighbors[i] = np.amin(ds)

    return Az, El, nearestNeighbors




def addSamplepoints(_inputGrid, nNewPoints, use_loop=True, _correctionGrid=None, force_sh_order=None):

    d2r = np.pi / 180
    r2d = 1 / d2r

    if _correctionGrid is None:
        _correctionGrid = makeGaussGrid(10, 10) * d2r

    inputGrid = _inputGrid * d2r
    correctionGrid = _correctionGrid * d2r

    nInputPoints = np.size(inputGrid, 0)
    nCorrectionPoints = np.size(correctionGrid, 0)
    #print("nINputPoints: ", nInputPoints, "  nCorrectionPoints: ", nCorrectionPoints)

    bestmatch = np.zeros(nNewPoints)
    if force_sh_order is None:
        sh_order = np.floor(np.sqrt((nNewPoints + nInputPoints)) - 2)
    else:
        sh_order = force_sh_order


    # get all combinations of n points
    combinations = itertools.combinations(range(nCorrectionPoints), nNewPoints)
    combinations = np.array(list(combinations))

    print("\nSearching through ", np.size(combinations, 0), " possible combinations of ", nCorrectionPoints, " points")
    print("Use Loop: ", use_loop)
    start_time = time.time()

    YnmBase = get_sph_harms(sh_order, inputGrid[:, 0], inputGrid[:, 1])

    condition = 100 # start value for the optimisation problem
    m, n = mnArrays(sh_order)
    for row in combinations:
        grid = np.vstack((inputGrid, correctionGrid[row, :]))
        grid = correctionGrid[row, :]
        if(use_loop == True):
            YnmCorr = get_sph_harms(sh_order, grid[:, 0], grid[:, 1])
        else:
            YnmCorr = sph_harm_all(sh_order, grid[:, 0], grid[:, 1], m, n)

        #make condition
        c = np.linalg.cond(np.vstack((YnmBase, YnmCorr)))

        if c < condition:
            bestmatch = row
            condition = c

    correction_points = correctionGrid[bestmatch]

    print("Took ", time.time() - start_time, " seconds")
    print("Best condition value found was ", condition, " for SH Order ", sh_order)

    return correction_points * r2d
