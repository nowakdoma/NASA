"""Tiny HTTP helpers: retrying downloads with atomic writes. Stdlib only, so the
dependency allow-list stays untouched (see AGENTS.md)."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "FieldShift/0.1 (NASA Space Apps 2026; offline decision support)"
RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


def download(
    url: str,
    dest: Path,
    *,
    timeout: float = 180.0,
    retries: int = 3,
    backoff: float = 2.0,
    force: bool = False,
    headers: dict[str, str] | None = None,
) -> Path:
    """Download ``url`` to ``dest``; skip when it already exists (idempotent).

    Writes to ``dest.part`` first so an interrupted run never leaves a truncated
    file that a later run would mistake for a complete download.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0 and not force:
        return dest

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        tmp = dest.with_name(dest.name + ".part")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as resp, open(tmp, "wb") as fh:
                while chunk := resp.read(1 << 16):
                    fh.write(chunk)
            if tmp.stat().st_size == 0:
                raise OSError(f"empty response body from {url}")
            tmp.replace(dest)
            return dest
        except urllib.error.HTTPError as err:
            last_err = err
            if err.code not in RETRY_STATUS:
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            last_err = err
        if attempt < retries:
            time.sleep(backoff * attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {url}") from last_err


def get_text(url: str, *, timeout: float = 120.0, retries: int = 3) -> str:
    """Fetch a small text/JSON resource with the same retry policy."""
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as err:
            last_err = err
            if err.code not in RETRY_STATUS:
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            last_err = err
        if attempt < retries:
            time.sleep(2.0 * attempt)
    raise RuntimeError(f"request failed after {retries} attempts: {url}") from last_err
