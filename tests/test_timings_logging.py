def test_topics_timings_event_preserves_browser_and_status():
    from litefupzl.oneshot.logging import PublicRecorder
    from litefupzl.oneshot.timings import record_topics_timing_status

    recorder = PublicRecorder("output/test-timings")

    record_topics_timing_status(
        recorder,
        slot_alias="slot-001",
        browser_name="patchright-chromium",
        status_code=429,
    )

    event = recorder.timeline[-1]
    assert event.step == "topics-timings"
    assert event.status == "observed"
    assert event.browser_core == "patchright-chromium"
    assert event.url_category == "/topics/timings"
    assert event.status_code == 429
    assert event.ts


def test_artifact_only_events_are_not_printed_to_public_log(capsys):
    from litefupzl.oneshot.logging import PublicRecorder, configure_public_logger

    recorder = PublicRecorder("output/test-artifact-only")

    with configure_public_logger():
        recorder.emit(
            "slot-001",
            "login-proof",
            "ok",
            code="SECURITY_PREFERENCES_OK",
            public=False,
        )
        recorder.emit("slot-001", "login-check", "ok")

    captured = capsys.readouterr()
    assert "login-check ok" in captured.err
    assert "login-proof" not in captured.err
    assert "SECURITY_PREFERENCES_OK" not in captured.err
    assert [event.step for event in recorder.timeline] == ["login-proof", "login-check"]
    assert recorder.timeline[0].public is False
    assert recorder.timeline[1].public is True


def test_public_logger_outputs_each_public_event_once(capsys):
    import sys

    from loguru import logger

    from litefupzl.oneshot.logging import PublicRecorder, configure_public_logger

    recorder = PublicRecorder("output/test-public-once")
    preexisting_handler = logger.add(sys.stderr, level="INFO", format="PREEXISTING {message}")

    try:
        with configure_public_logger():
            recorder.emit("system", "config", "loaded")
    finally:
        try:
            logger.remove(preexisting_handler)
        except ValueError:
            pass

    captured = capsys.readouterr()
    assert captured.err.count("system config loaded") == 1
    assert "PREEXISTING" not in captured.err
