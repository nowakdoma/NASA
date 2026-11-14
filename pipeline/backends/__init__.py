"""Backend registry: region key -> (CropHistorySource, SoilSource) factory."""

from __future__ import annotations

from collections.abc import Callable

from pipeline.backends.us import CdlCropHistory, SsurgoSoil
from pipeline.interfaces import CropHistorySource, SoilSource

REGISTRY: dict[str, Callable[[], tuple[CropHistorySource, SoilSource]]] = {
    "us": lambda: (CdlCropHistory(), SsurgoSoil()),
}


def get_backend(key: str) -> tuple[CropHistorySource, SoilSource]:
    try:
        return REGISTRY[key]()
    except KeyError as e:
        raise KeyError(f"unknown backend {key!r}; available: {sorted(REGISTRY)}") from e
