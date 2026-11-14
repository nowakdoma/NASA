"""Export engine results to contracts format in web/public/data/.

Scaffold behaviour: copy contracts/mock/* (validated) so the web app has data.
Later: build fields.geojson from pipeline outputs + strategies.json from engine models.
"""

from __future__ import annotations

import shutil
import sys

from engine import CONTRACTS, WEB_DATA
from engine.validate import validate_all

FILES = ("fields.geojson", "strategies.json")


def export_mock() -> None:
    """Validate the mocks and copy them to web/public/data."""
    errors = validate_all(CONTRACTS / "mock" / FILES[0], CONTRACTS / "mock" / FILES[1])
    if errors:
        raise SystemExit("mock data invalid:\n" + "\n".join(errors))
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copyfile(CONTRACTS / "mock" / name, WEB_DATA / name)
        print(f"exported {name} -> {WEB_DATA / name}")


def main(argv: list[str] | None = None) -> int:
    export_mock()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
