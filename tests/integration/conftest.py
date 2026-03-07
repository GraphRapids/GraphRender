"""Pytest fixtures for GraphRender integration tests.

Integration tests are **skipped** when the ``SERVICE_URL`` environment
variable is not set.  This ensures the default ``pytest`` invocation
only runs unit tests.

Usage::

    SERVICE_URL=http://localhost:8080 pytest tests/integration/ -v
"""

from __future__ import annotations

import os

import pytest

_SERVICE_URL_VAR = "SERVICE_URL"


@pytest.fixture()
def service_url() -> str:
    """Base URL of the running GraphRender service.

    Returns the value of ``SERVICE_URL`` or skips the test if the
    variable is not set.
    """
    url = os.environ.get(_SERVICE_URL_VAR)
    if not url:
        pytest.skip(f"{_SERVICE_URL_VAR} environment variable not set")
    return url.rstrip("/")
