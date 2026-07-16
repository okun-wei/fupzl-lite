from urllib.parse import quote, unquote


def normalize_cookie_value(value: str) -> str:
    """Normalize a cookie value to percent-encoded canonical form."""
    cleaned = (value or "").strip()
    if not cleaned:
        return cleaned
    return quote(unquote(cleaned), safe="")


def parse_cookies(cookie_str: str) -> list[dict]:
    """Parse cookie string into list of {name, value} dicts.

    Supports single or multiple cookies separated by '; '.
    Example: "_t=abc123; _forum_session=xyz789"

    Cookie values are normalized to percent-encoded form so Secrets may use
    either raw or already-encoded `_t` values interchangeably.
    """
    cookies = []
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            name, value = part.split("=", 1)
            cookies.append(
                {
                    "name": name.strip(),
                    "value": normalize_cookie_value(value.strip()),
                }
            )
    return cookies


def normalize_cookie_string(cookie_str: str) -> str:
    """Normalize all cookie values in a cookie header string."""
    parsed = parse_cookies(cookie_str)
    if not parsed:
        return cookie_str.strip()
    return "; ".join(f"{cookie['name']}={cookie['value']}" for cookie in parsed)
