"""Auth header selection: token beats username/password, and neither leaks into files."""

from __future__ import annotations

import base64

import pytest

from pipeline import config


@pytest.fixture(autouse=True)
def _no_real_dotenv(monkeypatch):
    """Never let the developer's .env decide what these tests assert."""
    monkeypatch.setattr(config, "load_env", lambda *a, **k: None)


def test_token_is_preferred_over_password(monkeypatch):
    monkeypatch.setenv("EARTHDATA_TOKEN", "abc123")
    monkeypatch.setenv("EARTHDATA_USERNAME", "alice")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "hunter2")
    assert config.earthdata_token() == "abc123"
    assert config.earthdata_auth_header() == {"Authorization": "Bearer abc123"}


def test_blank_token_falls_back_to_basic_auth(monkeypatch):
    monkeypatch.setenv("EARTHDATA_TOKEN", "   ")
    monkeypatch.setenv("EARTHDATA_USERNAME", "alice")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "hunter2")
    assert config.earthdata_token() is None
    expected = base64.b64encode(b"alice:hunter2").decode()
    assert config.earthdata_auth_header() == {"Authorization": f"Basic {expected}"}


def test_no_credentials_at_all_raises(monkeypatch):
    for key in ("EARTHDATA_TOKEN", "EARTHDATA_USERNAME", "EARTHDATA_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    assert config.earthdata_token() is None
    with pytest.raises(RuntimeError, match="EARTHDATA_USERNAME"):
        config.earthdata_auth_header()


def test_header_never_contains_the_raw_password_outside_base64(monkeypatch):
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    monkeypatch.setenv("EARTHDATA_USERNAME", "alice")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "hunter2")
    header = config.earthdata_auth_header()["Authorization"]
    assert "hunter2" not in header
