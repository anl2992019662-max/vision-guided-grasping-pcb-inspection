"""Optics exercises and planar image-to-robot calibration; not a 3-D hand-eye solver."""
import math
import numpy as np

def positive(value, name):
    x = float(value)
    if not math.isfinite(x) or x <= 0:
        raise ValueError(name + ' must be finite and positive')
    return x

def teaching_fov(sensor_width, sensor_height, working_distance, focal_length):
    """Taskbook approximation beta = h/H = f/WD, all dimensions in mm."""
    sw, sh, wd, f = [positive(v, n) for v, n in zip(
        [sensor_width, sensor_height, working_distance, focal_length], ['width','height','WD','focal length'])]
    return sw * wd / f, sh * wd / f

def focal_limit(sensor_width, sensor_height, working_distance, minimum_fov):
    sw, sh, wd, fw, fh = [positive(v, n) for v, n in zip(
        [sensor_width, sensor_height, working_distance, *minimum_fov], ['width','height','WD','FOV width','FOV height'])]
    horizontal, vertical = sw * wd / fw, sh * wd / fh
    return {'horizontal_limit_mm': horizontal, 'vertical_limit_mm': vertical,
            'both_axes_limit_mm': min(horizontal, vertical), 'formula': 'taskbook approximation'}

def fit_planar_affine(pixels, robot_xy):
    pixels = np.asarray(pixels, dtype=float)
    target = np.asarray(robot_xy, dtype=float)
    if pixels.ndim != 2 or pixels.shape[1] != 2 or pixels.shape != target.shape or len(pixels) < 3:
        raise ValueError('At least three paired 2-D points are required')
    if not np.isfinite(pixels).all() or not np.isfinite(target).all():
        raise ValueError('Calibration points must be finite')
    design = np.column_stack([pixels, np.ones(len(pixels))])
    if np.linalg.matrix_rank(design) < 3 or np.linalg.cond(design) > 1e8:
        raise ValueError('Calibration points are collinear or poorly conditioned')
    matrix, _, _, _ = np.linalg.lstsq(design, target, rcond=None)
    errors = np.linalg.norm(design @ matrix - target, axis=1)
    return {'matrix': matrix.T.tolist(), 'fit_rms_mm': float(np.sqrt(np.mean(errors ** 2))),
            'point_count': len(pixels), 'scope': 'planar affine fit; fit residual is not independent hardware accuracy'}

def transform_xy(matrix, point):
    m = np.asarray(matrix, dtype=float)
    p = np.asarray(point, dtype=float)
    if m.shape != (2,3) or p.shape != (2,) or not np.isfinite(m).all() or not np.isfinite(p).all():
        raise ValueError('Expected finite 2x3 matrix and 2-D point')
    return (m @ np.r_[p, 1.0]).tolist()
