"""Redaction helpers for public litefupzl logs and artifacts."""

from __future__ import annotations

import builtins
import json
import os
import re
import sys
from dataclasses import dataclass

from litefupzl.utils import normalize_cookie_value

COOKIE_PATTERN = re.compile(r"(?i)(_t=)([^;,\s]+)")
URL_PATTERN = re.compile(r"https?://[^\s]+")
USER_PATH_PATTERN = re.compile(r"/u/[A-Za-z0-9_\-]+")
TOPIC_PATH_PATTERN = re.compile(r"/t/[^/\s]+/\d+")
POST_ID_PATTERN = re.compile(r"\bpost\s+\d+\b", re.IGNORECASE)
TOPIC_ID_PATTERN = re.compile(r"\btopic\s+\d+\b", re.IGNORECASE)

REDACTED_COOKIES_JSON = "<redacted-cookies-json>"
REDACTED_COOKIE = "<redacted-cookie>"
REDACTED_ADMIN_TOKEN = "<redacted-admin-token>"
REDACTED_MUTUAL_LIKE_JSON = "<redacted-mutual-like-users>"
REDACTED_USERNAME = "<redacted-username>"

_COOKIE_ENV_KEYS = ("LITEFUPZL_COOKIES_JSON", "FUCKPZL_ONESHOT_COOKIES_JSON")
_ADMIN_TOKEN_ENV_KEYS = ("LITEFUPZL_ACTIONS_ADMIN_TOKEN", "FUCKPZL_ACTIONS_ADMIN_TOKEN")
_MUTUAL_LIKE_ENV_KEYS = ("LITEFUPZL_MUTUAL_LIKE_USERS_JSON",)


@dataclass(frozen=True)
class _SensitiveLiteral:
    value: str
    placeholder: str


_SENSITIVE_LITERALS: list[_SensitiveLiteral] = []
# Discourse's default minimum username length; word-boundary matches on shorter
# names would risk shredding ordinary log text.
_MIN_USERNAME_LEN = 2
# Usernames redact by word boundary (case-insensitive) rather than raw substring
# so a short name (e.g. "amy") can't corrupt unrelated words (e.g. "creamy").
_SENSITIVE_USERNAME_PATTERNS: list[tuple["re.Pattern[str]", str]] = []
_OUTPUT_HOOKS_INSTALLED = False
_ORIGINAL_PRINT = builtins.print
_ORIGINAL_STDOUT_WRITE = sys.stdout.write
_ORIGINAL_STDERR_WRITE = sys.stderr.write


def slot_alias(slot_index: int) -> str:
    """Return a stable public alias for a cookie slot."""
    return f"slot-{slot_index:03d}"


def mask_cookie(cookie: str) -> str:
    """Mask cookie values for internal debug use."""
    return COOKIE_PATTERN.sub(r"\1<redacted>", cookie)


def _register_literal(value: str | None, placeholder: str, bucket: list[_SensitiveLiteral]) -> None:
    cleaned = (value or "").strip()
    if not cleaned:
        return
    bucket.append(_SensitiveLiteral(value=cleaned, placeholder=placeholder))


def _register_json_array_literals(raw: str | None, *, json_placeholder: str, item_placeholder: str, bucket: list[_SensitiveLiteral]) -> None:
    _register_literal(raw, json_placeholder, bucket)
    if not raw:
        return
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return
    if not isinstance(parsed, list):
        return
    for item in parsed:
        _register_literal(str(item), item_placeholder, bucket)


def _json_escaped_variant(value: str | None) -> str | None:
    r"""Return the JSON-escaped body of a value when it differs from the raw form.

    Artifacts serialize secrets via json.dumps; non-ASCII (\uXXXX) escapes would
    otherwise slip past raw literal matching.
    """
    cleaned = (value or "").strip()
    if not cleaned:
        return None
    try:
        escaped = json.dumps(cleaned)[1:-1]
    except (TypeError, ValueError):
        return None
    return escaped if escaped != cleaned else None


def _json_array_items(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _bare_cookie_values(cookie_string: str) -> list[str]:
    """Yield the raw value(s) of each `name=value` pair in a cookie string."""
    values: list[str] = []
    for part in cookie_string.split(";"):
        part = part.strip()
        if "=" in part:
            _, value = part.split("=", 1)
            value = value.strip()
            if value:
                values.append(value)
    return values


def register_sensitive_env_literals() -> None:
    """Register the three sensitive env values and their parsed members for literal redaction."""
    literals: list[_SensitiveLiteral] = []
    username_patterns: list[tuple["re.Pattern[str]", str]] = []

    for key in _COOKIE_ENV_KEYS:
        raw = os.environ.get(key)
        _register_json_array_literals(
            raw,
            json_placeholder=REDACTED_COOKIES_JSON,
            item_placeholder=REDACTED_COOKIE,
            bucket=literals,
        )
        # Additive: also cover each bare cookie value in raw and normalized
        # (percent-encoded) forms plus their JSON-escaped variants, so a value
        # logged without the `_t=` prefix or after normalization is still hidden.
        for item in _json_array_items(raw):
            for cookie_value in _bare_cookie_values(item):
                for form in (cookie_value, normalize_cookie_value(cookie_value)):
                    _register_literal(form, REDACTED_COOKIE, literals)
                    _register_literal(_json_escaped_variant(form), REDACTED_COOKIE, literals)

    for key in _ADMIN_TOKEN_ENV_KEYS:
        token = os.environ.get(key)
        _register_literal(token, REDACTED_ADMIN_TOKEN, literals)
        _register_literal(_json_escaped_variant(token), REDACTED_ADMIN_TOKEN, literals)

    seen_usernames: set[str] = set()
    for key in _MUTUAL_LIKE_ENV_KEYS:
        raw = os.environ.get(key)
        _register_literal(raw, REDACTED_MUTUAL_LIKE_JSON, literals)
        for item in _json_array_items(raw):
            name = item.strip()
            if len(name) < _MIN_USERNAME_LEN or name in seen_usernames:
                continue
            seen_usernames.add(name)
            username_patterns.append(
                (re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE), REDACTED_USERNAME)
            )
            # Serialized artifacts escape non-ASCII names; cover that literal too.
            _register_literal(_json_escaped_variant(name), REDACTED_USERNAME, literals)

    deduped: dict[str, str] = {}
    for literal in literals:
        deduped.setdefault(literal.value, literal.placeholder)
    _SENSITIVE_LITERALS.clear()
    _SENSITIVE_LITERALS.extend(
        _SensitiveLiteral(value=value, placeholder=placeholder)
        for value, placeholder in deduped.items()
    )
    _SENSITIVE_USERNAME_PATTERNS.clear()
    _SENSITIVE_USERNAME_PATTERNS.extend(username_patterns)


def _apply_literal_redaction(text: str) -> str:
    if not _SENSITIVE_LITERALS and not _SENSITIVE_USERNAME_PATTERNS:
        return text
    for literal in sorted(_SENSITIVE_LITERALS, key=lambda item: len(item.value), reverse=True):
        if literal.value in text:
            text = text.replace(literal.value, literal.placeholder)
    for pattern, placeholder in _SENSITIVE_USERNAME_PATTERNS:
        text = pattern.sub(placeholder, text)
    return text


def redact_text(value: str) -> str:
    """Redact common sensitive tokens from arbitrary text."""
    text = value or ""
    text = _apply_literal_redaction(text)
    text = COOKIE_PATTERN.sub(r"\1<redacted>", text)
    text = URL_PATTERN.sub("<redacted-url>", text)
    text = USER_PATH_PATTERN.sub("/u/<redacted-user>", text)
    text = TOPIC_PATH_PATTERN.sub("/t/<redacted-topic>", text)
    text = POST_ID_PATTERN.sub("post <redacted>", text)
    text = TOPIC_ID_PATTERN.sub("topic <redacted>", text)
    return text


def _redact_stream_payload(data: str | bytes) -> str | bytes:
    if isinstance(data, bytes):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return data
        return redact_text(text).encode("utf-8")
    return redact_text(data)


def _guarded_print(*args, **kwargs):
    args = tuple(redact_text(arg) if isinstance(arg, str) else arg for arg in args)
    for key in ("sep", "end"):
        if key in kwargs and isinstance(kwargs[key], str):
            kwargs[key] = redact_text(kwargs[key])
    return _ORIGINAL_PRINT(*args, **kwargs)


def _guarded_stream_write(original_write):
    def write(data):
        return original_write(_redact_stream_payload(data))

    return write


def _install_output_hooks() -> None:
    global _OUTPUT_HOOKS_INSTALLED
    if _OUTPUT_HOOKS_INSTALLED:
        return
    builtins.print = _guarded_print
    sys.stdout.write = _guarded_stream_write(_ORIGINAL_STDOUT_WRITE)
    sys.stderr.write = _guarded_stream_write(_ORIGINAL_STDERR_WRITE)
    _OUTPUT_HOOKS_INSTALLED = True


def install_sensitive_output_guard() -> None:
    """Register sensitive env literals and hook stdout/stderr print paths."""
    register_sensitive_env_literals()
    _install_output_hooks()
