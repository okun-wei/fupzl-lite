import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_SRC = ROOT / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from click.exceptions import Exit
from litefupzl.oneshot.orchestrator import run_oneshot_sync


if __name__ == "__main__":
    try:
        run_oneshot_sync()
    except Exit as exc:
        raise SystemExit(exc.exit_code)
