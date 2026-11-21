#
#  Warp an image with a solved transformation matrix
#
# T maps image pixel coordinates to target coordinates (homogeneous, 3x3).
# Target units are 0.1 inch by default, and the output is rendered at 300 dpi,
# so one target unit is 30 output pixels.
#
# Coordinates: marker positions are scene coordinates, where pixel (i, j)
# covers [i, i+1) x [j, j+1), so its center is at (i+0.5, j+0.5).
#
# Sampling is bicubic (cubic B-spline). When the output has fewer pixels than
# the source, each
# output pixel is supersampled on a k x k grid and averaged, so detail is
# area-averaged instead of aliased.
#

import math
import os
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy import ndimage
from PySide6 import QtGui

UNITS_PER_INCH = 10.0       # target units are 0.1 inch
OUTPUT_DPI = 300.0
BORDER_GRAY = 128           # fill for output pixels outside the image
MAX_OUTPUT_SIDE = 20000     # refuse absurd sizes from a bad solution
MAX_SUPERSAMPLE = 8
_CHUNK_POINTS = 1 << 18     # sample points per band: bounds memory, and gives
                            # enough bands to keep every core busy
_WORKERS = os.cpu_count() or 1

def _toArray(image: QtGui.QImage) -> np.ndarray:
    img = image.convertToFormat(QtGui.QImage.Format.Format_RGB888)
    w, h = img.width(), img.height()
    buf = np.frombuffer(img.constBits(), dtype=np.uint8)
    return buf.reshape(h, img.bytesPerLine())[:, :w * 3].reshape(h, w, 3).copy()

def _toImage(arr: np.ndarray, dpi: float) -> QtGui.QImage:
    h, w, _ = arr.shape
    arr = np.ascontiguousarray(arr)
    image = QtGui.QImage(arr.data, w, h, 3 * w, QtGui.QImage.Format.Format_RGB888).copy()
    dpm = round(dpi / 0.0254)
    image.setDotsPerMeterX(dpm)
    image.setDotsPerMeterY(dpm)
    return image

def outputGeometry(width: int, height: int, T: np.ndarray, dpi: float = OUTPUT_DPI,
                   units_per_inch: float = UNITS_PER_INCH) -> tuple[np.ndarray, int, int]:
    # Returns M, the matrix from image coordinates to output pixel coordinates,
    # and the output size. Raises ValueError if the result can't be rendered.
    if not np.all(np.isfinite(T)):
        raise ValueError('The transformation is not finite')
    scale = dpi / units_per_inch
    M = np.diag([scale, scale, 1.0]) @ T
    print(M)
    corners = np.array([[0, width, width, 0], [0, 0, height, height], [1, 1, 1, 1]], dtype=float)
    p = M @ corners
    # A projective map keeps the image a convex quad only if no corner
    # crosses the horizon (w <= 0)
    if np.any(p[2] <= 0):
        raise ValueError('The transformation maps part of the image past the horizon')
    xs, ys = p[0] / p[2], p[1] / p[2]
    x0, y0 = math.floor(xs.min()), math.floor(ys.min())
    out_w = math.ceil(xs.max()) - x0
    out_h = math.ceil(ys.max()) - y0
    if out_w < 1 or out_h < 1:
        raise ValueError('The transformed image is empty')
    if max(out_w, out_h) > MAX_OUTPUT_SIDE:
        raise ValueError(f'The transformed image would be {out_w} x {out_h} pixels, which is too large')
    # Shift so the extents start at (0, 0)
    M = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]], dtype=float) @ M
    return M, out_w, out_h

def _supersample(width: int, height: int, M: np.ndarray, out_w: int, out_h: int) -> int:
    # Average linear minification, from the areas of the image and its output quad
    corners = np.array([[0, width, width, 0], [0, 0, height, height], [1, 1, 1, 1]], dtype=float)
    p = M @ corners
    xs, ys = p[0] / p[2], p[1] / p[2]
    quad_area = 0.5 * abs(np.dot(xs, np.roll(ys, -1)) - np.dot(ys, np.roll(xs, -1)))
    ratio = math.sqrt(width * height / max(quad_area, 1e-12))
    return max(1, min(MAX_SUPERSAMPLE, math.ceil(ratio)))

def warpImage(image: QtGui.QImage, T: np.ndarray, dpi: float = OUTPUT_DPI,
              units_per_inch: float = UNITS_PER_INCH) -> QtGui.QImage:
    # Raises ValueError if the transformation can't produce an image
    src = _toArray(image)
    h, w, _ = src.shape
    M, out_w, out_h = outputGeometry(w, h, T, dpi, units_per_inch)
    k = _supersample(w, h, M, out_w, out_h)
    Minv = np.linalg.inv(M)

    # Cubic spline coefficients, computed once per channel. scipy releases
    # the GIL in its C code, so the channels and bands below run in parallel.
    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        coeffs = list(pool.map(lambda c: ndimage.spline_filter(
            src[:, :, c].astype(np.float32), order=3, mode='mirror', output=np.float32), range(3)))

        out = np.empty((out_h, out_w, 3), dtype=np.uint8)
        ss_w = out_w * k
        band = max(1, _CHUNK_POINTS // (ss_w * k))   # output rows per band
        us = (np.arange(ss_w) + 0.5) / k              # subpixel centers, output pixels

        def warpBand(row0: int) -> None:
            rows = min(band, out_h - row0)
            vs = row0 + (np.arange(rows * k) + 0.5) / k
            U, V = np.meshgrid(us, vs)
            sx = Minv[0, 0] * U + Minv[0, 1] * V + Minv[0, 2]
            sy = Minv[1, 0] * U + Minv[1, 1] * V + Minv[1, 2]
            sw = Minv[2, 0] * U + Minv[2, 1] * V + Minv[2, 2]
            # Scene coordinates to array indices (pixel centers at integers)
            rr = sy / sw - 0.5
            cc = sx / sw - 0.5
            # The image covers indices [-0.5, n-0.5]; everything else is border.
            # Sampling extends the edges, so the outer half pixel is kept.
            inside = (rr >= -0.5) & (rr <= h - 0.5) & (cc >= -0.5) & (cc <= w - 0.5)
            # Only interpolate points inside the image
            coords = np.array([rr[inside], cc[inside]])
            samples = np.full(rr.shape, BORDER_GRAY, dtype=np.float64)
            for c in range(3):
                if coords.shape[1]:
                    samples[inside] = ndimage.map_coordinates(coeffs[c], coords, order=3,
                                                              mode='mirror', prefilter=False)
                # Average each k x k block into one output pixel
                block = samples.reshape(rows, k, out_w, k).mean(axis=(1, 3))
                out[row0:row0 + rows, :, c] = np.clip(np.rint(block), 0, 255)

        # Bands write disjoint rows of out; list() re-raises any worker error
        list(pool.map(warpBand, range(0, out_h, band)))
    return _toImage(out, dpi)
