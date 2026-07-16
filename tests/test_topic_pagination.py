from types import SimpleNamespace

import pytest


def _latest_payload(*topics: dict) -> dict:
    return {"topic_list": {"topics": list(topics)}}


def _topic(topic_id: int, *, unread_posts: int = 0, unseen: bool = False) -> dict:
    return {
        "id": topic_id,
        "title": f"redacted-{topic_id}",
        "slug": f"topic-{topic_id}",
        "unread_posts": unread_posts,
        "unseen": unseen,
        "closed": False,
        "archived": False,
        "tags": [],
        "category_id": 1,
    }


@pytest.mark.parametrize(
    ("duration_minutes", "expected_pages"),
    [
        (1, 1),
        (5, 1),
        (6, 2),
        (40, 8),
    ],
)
def test_latest_page_count_ceil_duration_by_five(duration_minutes, expected_pages):
    from litefupzl.oneshot.session import _latest_page_count_for_duration

    assert _latest_page_count_for_duration(duration_minutes) == expected_pages


def test_latest_topics_pages_fetches_first_n_pages_and_keeps_unread_filter(monkeypatch):
    from litefupzl.discourse import http_bypass

    observed_urls = []
    payloads = {
        "https://linux.do/latest.json": _latest_payload(
            _topic(100, unread_posts=1),
            _topic(101, unread_posts=0, unseen=False),
        ),
        "https://linux.do/latest.json?page=1": _latest_payload(
            _topic(102, unread_posts=0, unseen=True),
            _topic(100, unread_posts=2, unseen=True),
        ),
        "https://linux.do/latest.json?page=2": _latest_payload(
            _topic(103, unread_posts=3),
        ),
    }

    def fake_fetch_json(cookies, url, *, referer=None, user_agent=None):
        observed_urls.append(url)
        assert cookies == [{"name": "_t", "value": "redacted"}]
        assert referer == "https://linux.do"
        assert user_agent == "test-agent"
        return payloads[url]

    monkeypatch.setattr(http_bypass, "fetch_json", fake_fetch_json)

    topics = http_bypass.get_latest_topics_pages_via_http(
        [{"name": "_t", "value": "redacted"}],
        "https://linux.do",
        pages=3,
        user_agent="test-agent",
    )

    assert observed_urls == [
        "https://linux.do/latest.json",
        "https://linux.do/latest.json?page=1",
        "https://linux.do/latest.json?page=2",
    ]
    assert [topic.id for topic in topics] == [100, 102, 103]
    assert topics[0].unseen is True
    assert topics[0].unread_posts == 2


def test_latest_topics_pages_extends_for_explicit_unseen_and_skips_filtered_empty_page(monkeypatch):
    from litefupzl.discourse import http_bypass

    observed_urls = []
    payloads = {
        "https://linux.do/latest.json": _latest_payload(_topic(200, unread_posts=1, unseen=False)),
        "https://linux.do/latest.json?page=1": {
            "topic_list": {
                "topics": [
                    {
                        "id": 201,
                        "title": "filtered",
                        "slug": "filtered",
                        "closed": False,
                        "archived": False,
                        "tags": [],
                    }
                ]
            }
        },
        "https://linux.do/latest.json?page=2": _latest_payload(
            _topic(202, unseen=True),
            _topic(203, unseen=True),
        ),
    }

    def fake_fetch_json(_cookies, url, *, referer=None, user_agent=None):
        observed_urls.append(url)
        return payloads[url]

    monkeypatch.setattr(http_bypass, "fetch_json", fake_fetch_json)

    topics = http_bypass.get_latest_topics_pages_via_http(
        [{"name": "_t", "value": "redacted"}],
        "https://linux.do",
        pages=2,
        max_pages=3,
        minimum_unseen_topics=2,
    )

    assert observed_urls == list(payloads)
    assert [topic.id for topic in topics] == [200, 202, 203]
    assert [topic.id for topic in topics if topic.unseen] == [202, 203]


@pytest.mark.asyncio
async def test_build_topic_queue_uses_minimum_pages_target_and_prioritizes_unseen(monkeypatch):
    from litefupzl.oneshot import session

    captured = {}

    def fake_get_latest_topics_pages_via_http(
        cookies,
        base_url,
        *,
        pages,
        max_pages=None,
        minimum_unseen_topics=0,
        user_agent=None,
    ):
        captured["cookies"] = cookies
        captured["base_url"] = base_url
        captured["pages"] = pages
        captured["max_pages"] = max_pages
        captured["minimum_unseen_topics"] = minimum_unseen_topics
        captured["user_agent"] = user_agent
        return [
            session.Topic(
                id=1,
                title="seen",
                slug="seen",
                url="https://linux.do/t/seen/1",
                unread_posts=1,
                unseen=False,
                closed=False,
                archived=False,
                tags=[],
                category_id=1,
            ),
            session.Topic(
                id=2,
                title="new",
                slug="new",
                url="https://linux.do/t/new/2",
                unread_posts=0,
                unseen=True,
                closed=False,
                archived=False,
                tags=[],
                category_id=1,
            ),
        ]

    monkeypatch.setattr(session, "get_latest_topics_pages_via_http", fake_get_latest_topics_pages_via_http)

    config = SimpleNamespace(
        duration_minutes=6,
        topic_prefetch_pages=7,
        topic_prefetch_max_pages=10,
        new_topic_target_per_run=9,
    )
    result = await session._build_topic_queue([{"name": "_t", "value": "redacted"}], config, user_agent="test-agent")

    assert [topic.id for topic in result] == [2, 1]
    assert captured == {
        "cookies": [{"name": "_t", "value": "redacted"}],
        "base_url": "https://linux.do",
        "pages": 7,
        "max_pages": 10,
        "minimum_unseen_topics": 9,
        "user_agent": "test-agent",
    }


def test_topic_prefetch_page_range_keeps_duration_depth_within_configured_bounds():
    from litefupzl.oneshot.session import _topic_prefetch_page_range

    assert _topic_prefetch_page_range(
        SimpleNamespace(duration_minutes=6, topic_prefetch_pages=7, topic_prefetch_max_pages=10)
    ) == (7, 10)
    assert _topic_prefetch_page_range(
        SimpleNamespace(duration_minutes=40, topic_prefetch_pages=7, topic_prefetch_max_pages=10)
    ) == (8, 10)
    assert _topic_prefetch_page_range(
        SimpleNamespace(duration_minutes=120, topic_prefetch_pages=7, topic_prefetch_max_pages=10)
    ) == (10, 10)
