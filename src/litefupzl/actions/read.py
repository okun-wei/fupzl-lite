"""Human-like read-only scrolling behavior."""

from __future__ import annotations

import asyncio
import random
import time

from loguru import logger


async def human_like_scroll(
    page,
    max_duration_seconds: int | None = None,
    *,
    safety_timeout_seconds: int | None = None,
    bottom_dwell_seconds_range: tuple[float, float] = (2.0, 5.0),
) -> None:
    """Scroll through a topic page with human-like behavior.

    This read-only helper never clicks reaction/reply controls and has no write
    callback path.
    """
    start = time.monotonic()
    viewport = page.viewport_size or {"width": 1920, "height": 1080}
    vh = viewport["height"]
    hard_deadline = None
    if max_duration_seconds is not None:
        hard_deadline = start + max_duration_seconds
    elif safety_timeout_seconds is not None:
        hard_deadline = start + safety_timeout_seconds

    while True:
        if hard_deadline is not None and time.monotonic() >= hard_deadline:
            break
        if random.random() < 0.05:
            step = -random.randint(50, 200)
        else:
            step = random.randint(150, 500)

        try:
            await page.evaluate(f"window.scrollBy(0, {step})")
        except Exception as exc:
            logger.debug(f"Scroll step aborted due to page state change: {exc}")
            break

        if random.random() < 0.3:
            mx = random.randint(100, min(1200, viewport["width"] - 50))
            my = random.randint(100, min(800, vh - 50))
            try:
                await page.mouse.move(mx, my)
            except Exception as exc:
                logger.debug(f"Mouse move failed (non-critical): {exc}")

        pause_type = random.choices(["short", "medium", "long"], weights=[70, 25, 5])[0]
        if pause_type == "short":
            await asyncio.sleep(random.uniform(0.5, 2.0))
        elif pause_type == "medium":
            await asyncio.sleep(random.uniform(2.0, 5.0))
        else:
            await asyncio.sleep(random.uniform(5.0, 15.0))

        try:
            at_bottom = await page.evaluate(
                """() => {
                    if (!document.body) {
                        return false;
                    }
                    return window.scrollY + window.innerHeight >= document.body.scrollHeight - 100;
                }"""
            )
        except Exception as exc:
            logger.debug(f"Bottom detection aborted due to page state change: {exc}")
            break
        if at_bottom:
            min_dwell, max_dwell = bottom_dwell_seconds_range
            await asyncio.sleep(random.uniform(min_dwell, max_dwell))
            break

    logger.debug(f"Read scroll finished: {time.monotonic() - start:.1f}s elapsed")
