from litefupzl.utils import normalize_cookie_string, normalize_cookie_value, parse_cookies

_RAW_VALUE = "synthetic/value+plus=="
_ENCODED_VALUE = "synthetic%2Fvalue%2Bplus%3D%3D"


def test_normalize_cookie_value_accepts_raw_and_encoded_forms():
    assert normalize_cookie_value(_RAW_VALUE) == _ENCODED_VALUE
    assert normalize_cookie_value(_ENCODED_VALUE) == _ENCODED_VALUE


def test_parse_cookies_normalizes_values():
    raw_cookie = f"_t={_RAW_VALUE}"
    encoded_cookie = f"_t={_ENCODED_VALUE}"

    assert parse_cookies(raw_cookie) == [{"name": "_t", "value": _ENCODED_VALUE}]
    assert parse_cookies(encoded_cookie) == [{"name": "_t", "value": _ENCODED_VALUE}]


def test_normalize_cookie_string_rewrites_cookie_header():
    assert normalize_cookie_string(f"_t={_RAW_VALUE}") == f"_t={_ENCODED_VALUE}"
    assert normalize_cookie_string(f"_t={_ENCODED_VALUE}") == f"_t={_ENCODED_VALUE}"


def test_env_loader_normalizes_cookies_from_secret(monkeypatch):
    import json

    from litefupzl.oneshot.env_loader import load_oneshot_env

    monkeypatch.setenv("LITEFUPZL_COOKIES_JSON", json.dumps([f"_t={_RAW_VALUE}"]))
    monkeypatch.setattr(
        "litefupzl.oneshot.env_loader.OneShotEnvConfig",
        type("Cfg", (), {"model_validate": staticmethod(lambda config: config)}),
    )

    config = load_oneshot_env()
    assert config["cookies"] == [f"_t={_ENCODED_VALUE}"]
