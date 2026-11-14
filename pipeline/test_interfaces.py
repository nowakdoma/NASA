from pipeline.backends import get_backend
from pipeline.interfaces import CropHistorySource, SoilSource


def test_us_backend_implements_interfaces():
    crops, soil = get_backend("us")
    assert isinstance(crops, CropHistorySource)
    assert isinstance(soil, SoilSource)
