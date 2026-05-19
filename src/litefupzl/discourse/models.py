from dataclasses import dataclass
from datetime import datetime


@dataclass
class Topic:
    """A topic from Discourse JSON API."""
    id: int
    title: str
    slug: str
    url: str
    unread_posts: int
    unseen: bool
    closed: bool
    archived: bool
    tags: list[str]
    category_id: int


@dataclass
class UserInfo:
    """User info from /u/{username}.json."""
    username: str
    trust_level: int
    suspended_till: datetime | None
    silenced_till: datetime | None
