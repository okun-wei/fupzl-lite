def parse_cookies(cookie_str: str) -> list[dict]:
    """Parse cookie string into list of {name, value} dicts.
    
    Supports single or multiple cookies separated by '; '.
    Example: "_t=abc123; _forum_session=xyz789"
    """
    cookies = []
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            name, value = part.split("=", 1)
            cookies.append({"name": name.strip(), "value": value.strip()})
    return cookies
