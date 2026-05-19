"""Redacted GitHub secret persistence probe for Phase 3 cookie refresh.

This probe intentionally writes only to a dedicated throwaway probe secret, not
to the production oneshot cookie secret. It exercises the same GitHub secret
write helper used by cookie refresh and emits only non-sensitive metadata.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
CORE_SRC = ROOT / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from litefupzl.oneshot.github_sync import refresh_slot_cookie_secret_from_context

_BASE_URL = "https://linux.do"
_PROBE_SECRET_NAME = "LITEFUPZL_COOKIE_REFRESH_PROBE"


class _StaticCookieContext:
    def __init__(self, cookies: list[dict]):
        self._cookies = cookies

    async def cookies(self, urls):
        if urls != [_BASE_URL]:
            return []
        return self._cookies


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_probe_cookie_value() -> str:
    return f"probe-{secrets.token_hex(16)}"


def get_repository_secret_metadata(
    *,
    admin_token: str,
    repository: str,
    secret_name: str,
    api_url: str = "https://api.github.com",
) -> dict:
    owner, repo = repository.split("/", 1)
    req = Request(
        f"{api_url}/repos/{owner}/{repo}/actions/secrets/{secret_name}",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "litefupzl",
        },
    )
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        return {"status_code": exc.code}


async def _always_valid(_cookie_string: str) -> bool:
    return True


async def run_cookie_refresh_probe() -> int:
    output_dir = Path(os.environ.get("LITEFUPZL_OUTPUT_DIR") or os.environ.get("FUCKPZL_ONESHOT_OUTPUT_DIR") or "output/litefupzl")
    output_dir.mkdir(parents=True, exist_ok=True)

    admin_token = os.environ.get("LITEFUPZL_ACTIONS_ADMIN_TOKEN") or os.environ.get("FUCKPZL_ACTIONS_ADMIN_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    api_url = os.environ.get("GITHUB_API_URL") or "https://api.github.com"
    secret_name = os.environ.get("LITEFUPZL_COOKIE_REFRESH_PROBE_SECRET") or os.environ.get("FUCKPZL_COOKIE_REFRESH_PROBE_SECRET") or _PROBE_SECRET_NAME
    run_id = os.environ.get("GITHUB_RUN_ID") or "local"

    result = {
        "started_at": _now(),
        "secret_name": secret_name,
        "target_cookie_names": ["_t"],
        "secret_value_shape": "json-list-one-slot",
        "refreshed": False,
        "metadata_found": False,
        "metadata_updated_at_present": False,
        "finished_at": None,
    }

    try:
        if not admin_token or not repository:
            result["error_code"] = "COOKIE_REFRESH_PROBE_MISSING_GITHUB_ENV"
            return_code = 1
        else:
            original_cookie_string = f"_t=probe-original-{run_id}"
            refreshed_cookie_value = _new_probe_cookie_value()
            context = _StaticCookieContext([
                {"name": "_t", "value": refreshed_cookie_value, "domain": "linux.do", "path": "/"}
            ])
            refreshed = await refresh_slot_cookie_secret_from_context(
                context,
                original_cookie_string=original_cookie_string,
                cookie_strings=[original_cookie_string],
                slot_index=1,
                admin_token=admin_token,
                repository=repository,
                api_url=api_url,
                secret_name=secret_name,
                base_url=_BASE_URL,
                validate_cookie_string=_always_valid,
            )
            result["refreshed"] = bool(refreshed)
            metadata = get_repository_secret_metadata(
                admin_token=admin_token,
                repository=repository,
                secret_name=secret_name,
                api_url=api_url,
            )
            result["metadata_found"] = metadata.get("name") == secret_name
            result["metadata_updated_at_present"] = bool(metadata.get("updated_at"))
            return_code = 0 if (
                result["refreshed"]
                and result["metadata_found"]
                and result["metadata_updated_at_present"]
            ) else 1
    finally:
        result["finished_at"] = _now()
        (output_dir / "cookie_refresh_probe.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return return_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_cookie_refresh_probe()))
