"""Integration tests for the GraphRender /health endpoint."""

from __future__ import annotations

import json
import urllib.request


def test_health_returns_200_with_ok_status(service_url: str) -> None:
    """GET /health returns 200 with {"status": "ok"}."""
    req = urllib.request.Request(f"{service_url}/health", method="GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
        content_type = resp.headers.get("Content-Type", "")
        assert "application/json" in content_type
        body = json.loads(resp.read().decode("utf-8"))
        assert body == {"status": "ok"}


def test_health_is_idempotent(service_url: str) -> None:
    """Multiple consecutive calls to /health return identical results."""
    for _ in range(3):
        req = urllib.request.Request(f"{service_url}/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            body = json.loads(resp.read().decode("utf-8"))
            assert body == {"status": "ok"}
