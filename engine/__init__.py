"""FieldShift engine: per-field metrics for rotation strategies + MCDA, exported to contracts/.

Owner: person 1. Everything here is offline and deterministic given a seed.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = REPO_ROOT / "contracts"
WEB_DATA = REPO_ROOT / "web" / "public" / "data"

__all__ = ["REPO_ROOT", "CONTRACTS", "WEB_DATA"]
