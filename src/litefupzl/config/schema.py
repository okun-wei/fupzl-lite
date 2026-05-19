"""Minimal configuration schema for litefupzl."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator

from litefupzl.config.defaults import (
    FINGERPRINT_LOCALE,
    FINGERPRINT_TIMEZONE,
    FINGERPRINT_VIEWPORT,
)


class FingerprintConfig(BaseModel):
    viewport: list[int] = Field(default_factory=lambda: list(FINGERPRINT_VIEWPORT))
    timezone: str = FINGERPRINT_TIMEZONE
    locale: str = FINGERPRINT_LOCALE

    @field_validator("viewport")
    @classmethod
    def validate_viewport(cls, value: list[int]) -> list[int]:
        if len(value) != 2:
            raise ValueError("viewport must be [width, height]")
        if value[0] < 800:
            raise ValueError(f"viewport width must be >= 800, got {value[0]}")
        if value[1] < 600:
            raise ValueError(f"viewport height must be >= 600, got {value[1]}")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (KeyError, ValueError):
            raise ValueError(f"Invalid IANA timezone: {value}")
        return value
