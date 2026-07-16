import io
import json

from litefupzl.oneshot.redaction import (
    REDACTED_ADMIN_TOKEN,
    REDACTED_COOKIE,
    REDACTED_COOKIES_JSON,
    REDACTED_MUTUAL_LIKE_JSON,
    REDACTED_USERNAME,
    install_sensitive_output_guard,
    redact_text,
    register_sensitive_env_literals,
)


def test_register_sensitive_env_literals_redacts_all_three_groups(monkeypatch):
    cookies_json = json.dumps(["_t=secret-cookie-value"])
    users_json = json.dumps(["alice", "bob"])
    monkeypatch.setenv("LITEFUPZL_COOKIES_JSON", cookies_json)
    monkeypatch.setenv("LITEFUPZL_ACTIONS_ADMIN_TOKEN", "secret-admin-token")
    monkeypatch.setenv("LITEFUPZL_MUTUAL_LIKE_USERS_JSON", users_json)

    register_sensitive_env_literals()
    text = redact_text(
        " ".join(
            [
                cookies_json,
                "_t=secret-cookie-value",
                "secret-admin-token",
                users_json,
                "alice",
                "bob",
            ]
        )
    )

    assert "secret-cookie-value" not in text
    assert "secret-admin-token" not in text
    assert "alice" not in text
    assert "bob" not in text
    assert REDACTED_COOKIES_JSON in text
    assert REDACTED_COOKIE in text
    assert REDACTED_ADMIN_TOKEN in text
    assert REDACTED_MUTUAL_LIKE_JSON in text
    assert REDACTED_USERNAME in text


def test_install_sensitive_output_guard_hooks_print_and_stderr(monkeypatch):
    monkeypatch.setenv("LITEFUPZL_COOKIES_JSON", json.dumps(["_t=secret-cookie-value"]))
    monkeypatch.setenv("LITEFUPZL_ACTIONS_ADMIN_TOKEN", "secret-admin-token")
    monkeypatch.setenv("LITEFUPZL_MUTUAL_LIKE_USERS_JSON", json.dumps(["alice"]))

    install_sensitive_output_guard()
    buffer = io.StringIO()
    print("admin=secret-admin-token cookie=_t=secret-cookie-value user=alice", file=buffer)
    combined = buffer.getvalue()

    assert "secret-admin-token" not in combined
    assert "secret-cookie-value" not in combined
    assert "alice" not in combined
    assert REDACTED_ADMIN_TOKEN in combined
    assert REDACTED_COOKIE in combined
    assert REDACTED_USERNAME in combined


def test_bare_cookie_value_redacted_in_raw_and_encoded_forms(monkeypatch):
    from litefupzl.utils import normalize_cookie_value

    raw_value = "ab/cd+ef=="
    monkeypatch.setenv("LITEFUPZL_COOKIES_JSON", json.dumps([f"_t={raw_value}"]))
    register_sensitive_env_literals()

    encoded_value = normalize_cookie_value(raw_value)
    assert redact_text(raw_value) == REDACTED_COOKIE
    assert redact_text(encoded_value) == REDACTED_COOKIE


def test_username_redaction_is_word_bounded_and_case_insensitive(monkeypatch):
    monkeypatch.setenv("LITEFUPZL_MUTUAL_LIKE_USERS_JSON", json.dumps(["amy"]))
    register_sensitive_env_literals()

    out = redact_text("creamy Amy amy")
    assert "creamy" in out
    assert "Amy" not in out
    assert out.count(REDACTED_USERNAME) == 2


def test_non_ascii_username_redacted_after_json_serialization(monkeypatch):
    monkeypatch.setenv("LITEFUPZL_MUTUAL_LIKE_USERS_JSON", json.dumps(["b\u00f6b"]))
    register_sensitive_env_literals()

    artifact = json.dumps({"liked_user": "b\u00f6b"})
    out = redact_text(artifact)
    assert "b\\u00f6b" not in out
    assert REDACTED_USERNAME in out


def test_load_oneshot_env_installs_output_guard(monkeypatch):
    from litefupzl.oneshot import env_loader

    monkeypatch.setenv("LITEFUPZL_COOKIES_JSON", json.dumps(["_t=secret-cookie-value"]))
    monkeypatch.setenv("LITEFUPZL_ACTIONS_ADMIN_TOKEN", "secret-admin-token")
    monkeypatch.setenv("LITEFUPZL_MUTUAL_LIKE_USERS_JSON", json.dumps(["alice"]))
    monkeypatch.setattr(env_loader, "OneShotEnvConfig", type("Cfg", (), {"model_validate": staticmethod(lambda config: config)}))

    env_loader.load_oneshot_env()
    buffer = io.StringIO()
    print("admin=secret-admin-token user=alice", file=buffer)
    combined = buffer.getvalue()

    assert "secret-admin-token" not in combined
    assert "alice" not in combined
    assert REDACTED_ADMIN_TOKEN in combined
    assert REDACTED_USERNAME in combined
