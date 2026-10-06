"""Pure-NumPy stand-in for the two moocore functions pymoo 0.6.1 imports.

moocore is a compiled (cffi/C) package that has no WebAssembly build, so it cannot run in
Pyodide. pymoo only uses it for exact hypervolume, which is a deterministic quantity, so this
module computes the same exact value (minimisation, points that do not strictly dominate the
reference point are ignored).
"""
import numpy as np


def _hv2d(P, ref):
    # P: points strictly better than ref in both objectives
    if len(P) == 0:
        return 0.0
    P = P[np.argsort(P[:, 0], kind="stable")]
    hv, best_y = 0.0, ref[1]
    for x, y in P:
        if y < best_y:
            hv += (ref[0] - x) * (best_y - y)
            best_y = y
    return hv


def _hv(P, ref):
    P = P[np.all(P < ref, axis=1)]
    d = P.shape[1] if P.ndim == 2 else len(ref)
    if len(P) == 0:
        return 0.0
    if d == 1:
        return float(ref[0] - P[:, 0].min())
    if d == 2:
        return _hv2d(P, ref)
    # slice along the last objective: sweep from best to worst, adding the (d-1)-dim hypervolume of
    # all points seen so far for each slab of thickness (next level - this level)
    order = np.argsort(P[:, -1], kind="stable")
    P = P[order]
    total = 0.0
    for i in range(len(P)):
        top = P[i + 1, -1] if i + 1 < len(P) else ref[-1]
        thickness = top - P[i, -1]
        if thickness > 0:
            total += _hv(P[: i + 1, :-1], ref[:-1]) * thickness
    return total


def hypervolume(data, ref):
    data = np.atleast_2d(np.asarray(data, dtype=float))
    ref = np.asarray(ref, dtype=float)
    return float(_hv(data, ref))


def hv_contributions(data, ref):
    data = np.atleast_2d(np.asarray(data, dtype=float))
    total = hypervolume(data, ref)
    out = np.empty(len(data))
    for k in range(len(data)):
        out[k] = total - hypervolume(np.delete(data, k, axis=0), ref)
    return out
