"""CLI: python -m pipeline {power,ndvi,smap,srtm,cdl,ssurgo,all}"""

from __future__ import annotations

import argparse
import sys

from pipeline.config import Config
from pipeline.sources import SOURCES


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m pipeline", description=__doc__)
    ap.add_argument("source", choices=[*SOURCES, "all"])
    args = ap.parse_args(argv)
    cfg = Config()
    names = list(SOURCES) if args.source == "all" else [args.source]
    pending = 0
    for name in names:
        try:
            SOURCES[name](cfg)
            print(f"[ok]   {name}")
        except NotImplementedError:
            pending += 1
            print(f"[todo] {name}: not implemented yet")
    print(f"{len(names) - pending}/{len(names)} sources done ({cfg.region.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
