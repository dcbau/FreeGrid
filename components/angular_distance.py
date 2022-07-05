import numpy as np

# equivalent to MATLAB sph2cart & cart2sph
def cart2sph(x,y,z):
    azimuth = np.arctan2(y,x)
    elevation = np.arctan2(z,np.sqrt(x**2 + y**2))
    r = np.sqrt(x**2 + y**2 + z**2)
    return azimuth, elevation, r

def sph2cart(azimuth,elevation,r):
    x = r * np.cos(elevation) * np.cos(azimuth)
    y = r * np.cos(elevation) * np.sin(azimuth)
    z = r * np.sin(elevation)
    return x, y, z

# get the angular distances from a single point to a list of points
def getDistances(p_az, p_el, grid_az, grid_el, input_format='deg', return_format='rad'):

    if input_format == 'deg':
        p_az = p_az * np.pi / 180
        p_el = p_el * np.pi / 180
        grid_az = grid_az * np.pi / 180
        grid_el = grid_el * np.pi / 180

    x1, y1, z1 = sph2cart(p_az, p_el, 1);
    x2, y2, z2 = sph2cart(grid_az, grid_el, 1);

    # make the single point value a matrix with same dimensions as the grid
    x1 = x1 * np.ones_like(x2)
    y1 = y1 * np.ones_like(z2)
    z1 = z1 * np.ones_like(z2)

    dotProduct = np.einsum('ji,ji->i', [x1, y1, z1], [x2, y2, z2])

    distances = np.arccos(np.clip(dotProduct, -1.0, 1.0));

    if return_format == 'deg':
        distances = distances * 180 / np.pi

    return distances

# get the angular distance from one point to another
def angularDistance(az1, el1, az2, el2, input_format='deg', return_format='deg'):


    if input_format == 'deg':
        az1 = az1 * np.pi / 180
        az2 = az2 * np.pi / 180
        el1 = el1 * np.pi / 180
        el2 = el2 * np.pi / 180

    x1, y1, z1 = sph2cart(az1, el1, 1);
    x2, y2, z2 = sph2cart(az2, el2, 1);

    # distance = np.arctan2(np.linalg.norm(np.cross(xyz1, xyz2)), np.dot(xyz1, xyz2)) / 180;
    distance = np.arccos(np.clip(np.dot([x1, y1, z1], [x2, y2, z2]), -1.0, 1.0));
    # distance = np.arccos(np.clip(0.5, -1.0, 1.0)) / np.pi;

    if return_format == 'deg':
        distance = distance * 180 / np.pi

    return distance