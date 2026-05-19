"""Browser fingerprint configuration.

Applies viewport, timezone, and locale settings when launching a persistent context.
These settings are passed as keyword arguments to launch_persistent_context().
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litefupzl.config.schema import FingerprintConfig


def build_context_options(fingerprint: FingerprintConfig) -> dict:
    """Build Playwright launch_persistent_context kwargs from fingerprint config."""
    return {
        "viewport": {
            "width": fingerprint.viewport[0],
            "height": fingerprint.viewport[1],
        },
        "locale": fingerprint.locale,
        "timezone_id": fingerprint.timezone,
    }
