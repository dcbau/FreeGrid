import numpy as np
from scipy import special as sp
from grid_improving.grid_creation import *
import itertools
import time
import sound_field_analysis.lebedev
import grid_improving.angular_distance


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

        ds = grid_improving.angular_distance.getDistances(Az[i], 90 - El[i], inputGrid[:, 0], 90 - inputGrid[:, 1])
        nearestNeighbors[i] = np.amin(ds)

    return Az, El, nearestNeighbors




def addSamplepoints(_inputGrid, nNewPoints, use_loop=True, _correctionGrid=None, force_sh_order=None):

    #convention: el = 0..180°

    d2r = np.pi / 180
    r2d = 1 / d2r

    if _correctionGrid is None:
        lebedev_grid = sound_field_analysis.lebedev.genGrid(194)
        az, el, r = grid_improving.angular_distance.cart2sph(lebedev_grid.x, lebedev_grid.y, lebedev_grid.z)
        az = az * r2d
        el = el * r2d
        az = az % 360
        el = 90 - el
        _correctionGrid = np.transpose(np.array([az, el]))

    inputGrid = _inputGrid * d2r
    correctionGrid = _correctionGrid * d2r

    nInputPoints = np.size(inputGrid, 0)
    nCorrectionPoints = np.size(correctionGrid, 0)

    bestmatch = np.zeros(nNewPoints).astype(dtype=int)
    if force_sh_order is None:
        sh_order = np.floor(np.sqrt((nNewPoints + nInputPoints)) - 2)
        if sh_order < 1:
            sh_order = 1
    else:
        sh_order = force_sh_order


    # get all combinations of n points
    combinations = itertools.combinations(range(nCorrectionPoints), nNewPoints)
    combinations = np.array(list(combinations))

    #print("\nSearching through ", np.size(combinations, 0), " possible combinations of ", nCorrectionPoints, " points")
    #print("Use Loop: ", use_loop)
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

    #print("Took ", time.time() - start_time, " seconds")
    #print("Best condition value found was ", condition, " for SH Order ", sh_order)

    return correction_points * r2d


def addSamplepoints_geometric(_inputGrid, nNewPoints, _correctionGrid=None):

    #convention: el = 0..180°

    d2r = np.pi / 180
    r2d = 1 / d2r

    if _correctionGrid is None:
        lebedev_grid = sound_field_analysis.lebedev.genGrid(194)
        az, el, r = grid_improving.angular_distance.cart2sph(lebedev_grid.x, lebedev_grid.y, lebedev_grid.z)
        az = az*r2d
        el = el*r2d
        az = az % 360
        el = 90 - el
        _correctionGrid = np.transpose(np.array([az, el]))

    inputGrid = _inputGrid# * d2r
    correctionGrid = _correctionGrid# * d2r

    nInputPoints = np.size(inputGrid, 0)
    nCorrectionPoints = np.size(correctionGrid, 0)



    # get all combinations of n points
    combinations = itertools.combinations(range(nCorrectionPoints), nNewPoints)
    combinations = np.array(list(combinations))

    #("\nSearching through ", np.size(combinations, 0), " possible combinations of ", nCorrectionPoints, " points")
    start_time = time.time()

    highest_min_distance = 0
    bestmatch = np.zeros(nNewPoints).astype(dtype=int)

    for row in combinations:
        min_distance = 180

        grid = correctionGrid[row, :]

        for i in range(nNewPoints):
            for j in range(np.size(inputGrid, 0)):
                d = grid_improving.angular_distance.angularDistance(inputGrid[j, 0], 90 - inputGrid[j, 1], grid[i, 0], 90 - grid[i, 1], return_format='deg')
                if d < min_distance:
                    min_distance = d



        new_point_combis = itertools.combinations(range(nNewPoints), 2)
        for c in new_point_combis:
            p1 = grid[c[0], :]
            p2 = grid[c[1], :]
            d = grid_improving.angular_distance.angularDistance(p1[0], 90 - p1[1], p2[0], 90 - p2[1])
            if d < min_distance:
                min_distance = d

        if min_distance > highest_min_distance:
            highest_min_distance = min_distance
            bestmatch = row

    correction_points = correctionGrid[bestmatch]

    #print("Took ", time.time() - start_time, " seconds")

    return correction_points

