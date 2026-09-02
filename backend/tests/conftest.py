"""Test configuration for backend unit tests."""
from __future__ import annotations

import sys
from pathlib import Path


def _ensure_path(path: Path) -> None:
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.append(str_path)


REPO_ROOT = Path(__file__).resolve().parents[2]
ENSURE_PATHS = [REPO_ROOT, REPO_ROOT / "backend"]

for candidate in ENSURE_PATHS:
    _ensure_path(candidate)
