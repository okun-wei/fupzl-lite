import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def isolate_env_loader_from_repo_dotenv(monkeypatch):
    """Keep local .env/.env.local out of unit tests; CI and dev shells still load them."""
    monkeypatch.setattr("litefupzl.oneshot.env_loader._load_repo_env_files", lambda: None)
