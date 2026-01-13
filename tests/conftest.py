"""Pytest configuration for notifier tests in the monorepo.

Ensures the repo root is importable so tests can import sibling packages like `control/`.
"""

from __future__ import annotations

import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)


def pytest_configure(config) -> None:
    # Mark registration to avoid warnings when running without pytest-asyncio.
    config.addinivalue_line("markers", "asyncio: asyncio-based test (runs via anyio backend)")


try:
    import pytest
except Exception:  # pragma: no cover
    pytest = None  # type: ignore[assignment]


if pytest is not None:

    @pytest.fixture
    def anyio_backend():
        """Run anyio-marked tests with asyncio only (trio is not required)."""
        return "asyncio"
