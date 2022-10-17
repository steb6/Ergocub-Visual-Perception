import copy
import importlib
import os
import types
from functools import reduce

import cv2
import numpy as np

try:
    from open3d.cuda.pybind.geometry import PointCloud
    from open3d.cuda.pybind.utility import Vector3dVector
    from open3d.cuda.pybind.visualization import draw_geometries
except ImportError:
    from open3d.cpu.pybind.geometry import PointCloud
    from open3d.cpu.pybind.utility import Vector3dVector
    from open3d.cpu.pybind.visualization import draw_geometries

def draw_pcs(*pcs):
    res = []
    for pc in pcs:
        o3d_pc = PointCloud()
        o3d_pc.points = Vector3dVector(pc)
        o3d_pc.paint_uniform_color(np.random.rand(3))
        res.append(o3d_pc)
    draw_geometries(res)


def draw_mask(rgb, mask):
    overlay = copy.deepcopy(rgb)
    if np.any(mask == 1):
        overlay[mask == 1] = np.array([0, 0, 128])
    res1 = cv2.addWeighted(rgb, 1, overlay, 0.5, 0)

    # res2 = copy.deepcopy(rgb)
    # res2[mask == 0] = np.array([0, 0, 0])

    return res1
    # return cv2.cvtColor(res1, cv2.COLOR_RGB2BGR) #, cv2.cvtColor(res2, cv2.COLOR_RGB2BGR)


def compose(*func):
    """Takes a list of function and returns a single function
        that applies them in order. If func is [f1, f2, f3] the functions
        will be applied as f3(f2(f1(x)))
    """
    def aux_compose(f, g):
        return lambda x: f(g(x))
    func = list(func)
    func.reverse()
    return reduce(aux_compose, func, lambda x: x)


def compose_transformations(tfs):
    """'All 3x3 matrices are padded with an additional row and column from the Identity Matrix
        All the 1x3 matrices are"""
    c = np.eye(4)

    for t in tfs:
        if not isinstance(t, np.ndarray):
            raise ValueError('Transformations must be numpy.ndarray.')

        if t.shape == (4, 4):
            pass
        elif t.shape == (3, 3):
            t = np.block([[t, np.zeros([3, 1])],
                          [np.zeros([1, 3]), np.ones([1, 1])]])
        elif t.shape == (1, 3):
            t = np.block([[np.eye(3), np.zeros([3, 1])],
                          [t, np.ones([1, 1])]])
        else:
            raise ValueError(f'Shape {t.shape} not allowed.')

        c = c @ t

    return c


def reload_package(package):
    assert(hasattr(package, "__package__"))
    fn = package.__file__
    fn_dir = os.path.dirname(fn) + os.sep
    module_visit = {fn}
    del fn

    def reload_recursive_ex(module):

        for module_child in vars(module).values():
            if isinstance(module_child, types.ModuleType):
                fn_child = getattr(module_child, "__file__", None)

                if (fn_child is not None) and fn_child.startswith(fn_dir):
                    if fn_child not in module_visit:
                        print("reloading:", fn_child, "from", module)
                        module_visit.add(fn_child)
                        reload_recursive_ex(module_child)

        importlib.reload(module)

    return reload_recursive_ex(package)

def plot_plane(a, b, c, d):
    xy = (np.random.rand(1000000, 2) - 0.5) * 2
    z = - ((a * xy[..., 0] + b * xy[..., 1] + d) / c)

    xy = xy[(-1 < z) & (z < 1)]
    z = z[(-1 < z) & (z < 1)]

    plane = np.concatenate([xy, z[..., None]], axis=1)

    aux = PointCloud()
    aux.points = Vector3dVector(plane)
    return aux

def plot_line(line):
    t = (np.random.rand(1000000, 1) - 0.5) * 2
    l0, l = line

    return l0 + t * l