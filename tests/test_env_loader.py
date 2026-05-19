import json

import pytest


def test_env_loader_requires_only_cookie_and_no_like_lottery(monkeypatch):
    from litefupzl.oneshot.env_loader import load_oneshot_env

    monkeypatch.setenv("LITEFUPZL_COOKIES_JSON", json.dumps(["_t=redacted"]))
    monkeypatch.delenv("FUCKPZL_ONESHOT_LOTTERY_TEXTS_JSON", raising=False)
    monkeypatch.delenv("FUCKPZL_ONESHOT_LOTTERY_EMOJIS_JSON", raising=False)
    monkeypatch.delenv("FUCKPZL_ONESHOT_LIKE_ENABLED", raising=False)
    monkeypatch.delenv("FUCKPZL_ONESHOT_LOTTERY_ENABLED", raising=False)

    config = load_oneshot_env()

    assert config.cookies == ["_t=redacted"]
    assert config.duration_minutes == 40
    assert config.cookie_refresh_enabled is False
    assert not hasattr(config, "like_enabled")
    assert not hasattr(config, "lottery_enabled")
    assert not hasattr(config, "lottery_texts")
    assert not hasattr(config, "lottery_emojis")


def test_scheduled_cookie_refresh_is_forced_disabled(monkeypatch):
    from litefupzl.oneshot.env_loader import load_oneshot_env

    monkeypatch.setenv("LITEFUPZL_COOKIES_JSON", json.dumps(["_t=redacted"]))
    monkeypatch.setenv("LITEFUPZL_COOKIE_REFRESH_ENABLED", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")

    config = load_oneshot_env()

    assert config.cookie_refresh_enabled is False


def test_manual_cookie_refresh_can_opt_in(monkeypatch):
    from litefupzl.oneshot.env_loader import load_oneshot_env

    monkeypatch.setenv("LITEFUPZL_COOKIES_JSON", json.dumps(["_t=redacted"]))
    monkeypatch.setenv("LITEFUPZL_COOKIE_REFRESH_ENABLED", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")

    config = load_oneshot_env()

    assert config.cookie_refresh_enabled is True


def test_legacy_cookie_env_alias_is_still_supported(monkeypatch):
    from litefupzl.oneshot.env_loader import load_oneshot_env

    monkeypatch.delenv("LITEFUPZL_COOKIES_JSON", raising=False)
    monkeypatch.setenv("FUCKPZL_ONESHOT_COOKIES_JSON", json.dumps(["_t=legacy-redacted"]))

    config = load_oneshot_env()

    assert config.cookies == ["_t=legacy-redacted"]
