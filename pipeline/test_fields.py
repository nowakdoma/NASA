"""Field delineation helpers: shape filters, majority vote and crop-code mapping.

The raster paths are exercised by `python -m pipeline fields`; these tests pin the
arithmetic that decides which polygons become fields.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from shapely.geometry import Point

from pipeline import fields


def test_circle_is_circularity_one():
    radius = 10.0
    area = math.pi * radius**2
    perimeter = 2 * math.pi * radius
    assert fields.circularity(area, perimeter) == pytest.approx(1.0)


def test_square_is_about_0785():
    side = 100.0
    assert fields.circularity(side * side, 4 * side) == pytest.approx(math.pi / 4)


def test_degenerate_perimeter_does_not_divide_by_zero():
    assert fields.circularity(0.0, 0.0) == 0.0


def test_majority_ignores_background_pixels():
    counts = np.zeros(256, dtype=np.int64)
    counts[0] = 900  # nodata/background dominates the polygon's bounding box
    counts[1] = 60  # corn
    counts[24] = 40  # winter wheat
    code, share = fields.majority_code(counts)
    assert code == 1
    # Share is of all pixels, so background stays visible in the purity number.
    assert share == pytest.approx(0.06)


def test_majority_of_empty_field_is_none():
    assert fields.majority_code(np.zeros(256, dtype=np.int64)) == (None, 0.0)


def test_majority_of_background_only_is_none():
    counts = np.zeros(256, dtype=np.int64)
    counts[0] = 500
    assert fields.majority_code(counts) == (None, 0.0)


def test_real_crops_csv_maps_the_documented_codes():
    mapping = fields.read_cdl_code_map()
    assert mapping[1] == "corn"
    assert mapping[5] == "soybeans"
    assert mapping[24] == "winter_wheat"
    assert mapping[36] == "alfalfa"
    assert mapping[61] == "fallow"
    assert mapping[176] == "grass_pasture"
    # CDL classes with no crops.csv row must not be invented.
    assert 121 not in mapping  # developed
    assert 111 not in mapping  # open water


def test_field_polygon_measured_in_metres():
    """EPSG:5070 areas are metres^2, so a 400 m pivot is ~12.6 ha of radius, 50 ha of area."""
    pivot = Point(0, 0).buffer(400, quad_segs=64)  # 400 m radius circle
    assert fields.circularity(pivot.area, pivot.length) > 0.99
    assert pivot.area / 10_000 == pytest.approx(50.0, abs=1.0)
