from litefupzl.utils import normalize_cookie_string, normalize_cookie_value, parse_cookies

_RAW_VALUE = (
    "BoK2pFajVrlkaMuZsMrI9lbmLs3WzxsOHfE1GYI7vBNC/naq5PNakDrVI/er8e6cNgGnP4xJWdS4ALRk9Mt7PjbTEsYXo8no3THY5E5698xAcHb3Twr3du"
    "+URX//I/usTTa6Ng7ULAwcZL/8PzlP8uI7BAJOR91W7vjPKQ5KeorsGhah0wEG4LP6CTmCrYnxWFppLepM0i6Qk5fzXZFVLjsK8eJh83dxZIBcSwfAOpp4dUI"
    "/DsC1djKkYaght+6o/f0b7YW72WjO77xfTDvTkSMvbh44kDTw--Pa/5woWrm9tYKGJl--ESaokz/AhD503wHvBrmZww=="
)
_ENCODED_VALUE = (
    "BoK2pFajVrlkaMuZsMrI9lbmLs3WzxsOHfE1GYI7vBNC%2Fnaq5PNakDrVI%2Fer8e6cNgGnP4xJWdS4ALRk9Mt7PjbTEsYXo8no3THY5E5698xAcHb3Twr3du"
    "%2BURX%2F%2FI%2FusTTa6Ng7ULAwcZL%2F8PzlP8uI7BAJOR91W7vjPKQ5KeorsGhah0wEG4LP6CTmCrYnxWFppLepM0i6Qk5fzXZFVLjsK8eJh83dxZIBcSwfAOpp4dUI"
    "%2FDsC1djKkYaght%2B6o%2Ff0b7YW72WjO77xfTDvTkSMvbh44kDTw--Pa%2F5woWrm9tYKGJl--ESaokz%2FAhD503wHvBrmZww%3D%3D"
)


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
