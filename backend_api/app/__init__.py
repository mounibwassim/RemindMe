"""FastAPI backend for the RemindMe Flutter migration."""

import sys
from pathlib import Path


def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "backend_api").exists():
            return parent
    return current.parent.parent.parent

PROJECT_ROOT = _find_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
