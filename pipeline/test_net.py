"""Idempotency of the download helper — the pipeline must be safe to re-run."""

from __future__ import annotations

import urllib.request

from pipeline import net


def test_existing_file_is_not_downloaded_again(tmp_path, monkeypatch):
    dest = tmp_path / "cached.csv"
    dest.write_text("already here")

    def explode(*args, **kwargs):
        raise AssertionError("download() hit the network for a cached file")

    monkeypatch.setattr(urllib.request, "urlopen", explode)
    assert net.download("https://example.invalid/x.csv", dest) == dest
    assert dest.read_text() == "already here"


def test_force_redownloads(tmp_path, monkeypatch):
    dest = tmp_path / "cached.csv"
    dest.write_text("stale")

    class FakeResp:
        def __init__(self, body: bytes):
            self._body = body

        def read(self, size: int = -1) -> bytes:
            body, self._body = self._body, b""
            return body

        def __enter__(self) -> FakeResp:
            return self

        def __exit__(self, *exc) -> None:
            return None

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: FakeResp(b"fresh"))
    net.download("https://example.invalid/x.csv", dest, force=True)
    assert dest.read_text() == "fresh"
