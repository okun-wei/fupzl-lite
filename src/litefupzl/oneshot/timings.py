"""Public-safe /topics/timings status logging helpers."""

from __future__ import annotations

from litefupzl.oneshot.logging import PublicRecorder

TIMINGS_URL_CATEGORY = "/topics/timings"


def record_topics_timing_status(
    recorder: PublicRecorder,
    *,
    slot_alias: str,
    browser_name: str,
    status_code: int | None,
) -> None:
    """Record a redacted per-browser /topics/timings status observation."""
    recorder.emit(
        slot_alias,
        "topics-timings",
        "observed",
        code=f"HTTP_{status_code}" if status_code is not None else "HTTP_UNKNOWN",
        browser_core=browser_name,
        url_category=TIMINGS_URL_CATEGORY,
        status_code=status_code,
    )


def attach_topics_timing_observer(page, recorder: PublicRecorder, slot_alias: str, browser_name: str) -> None:
    """Attach a Playwright response listener for public-safe /topics/timings statuses."""
    if getattr(page, "_litefupzl_topic_timings_observer_attached", False):
        return
    setattr(page, "_litefupzl_topic_timings_observer_attached", True)

    def on_response(response) -> None:
        if TIMINGS_URL_CATEGORY not in response.url:
            return
        record_topics_timing_status(
            recorder,
            slot_alias=slot_alias,
            browser_name=browser_name,
            status_code=response.status,
        )

    page.on("response", on_response)
