"""Integration tests for the GraphRender /render endpoint."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest


def test_render_minimal_graph(service_url: str) -> None:
    """POST /render with a minimal ELK graph returns valid SVG."""
    graph = {
        "id": "root",
        "width": 100,
        "height": 100,
        "children": [],
        "edges": [],
    }
    payload = json.dumps(graph).encode("utf-8")
    req = urllib.request.Request(
        f"{service_url}/render",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200
        body = resp.read().decode("utf-8")
        assert "<svg" in body


def test_render_rejects_invalid_json(service_url: str) -> None:
    """POST /render with invalid JSON returns 400."""
    payload = b"{not valid json}"
    req = urllib.request.Request(
        f"{service_url}/render",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=10)
    assert exc_info.value.code == 400


def test_render_error_does_not_leak_internals(service_url: str) -> None:
    """Server errors must not expose stack traces or internal details."""
    # Send syntactically valid JSON that is not a valid ELK graph.
    payload = json.dumps({"bad": True}).encode("utf-8")
    req = urllib.request.Request(
        f"{service_url}/render",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            # If the renderer happens to handle it gracefully, that is fine.
            _ = resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        # Must never contain Python tracebacks.
        assert "Traceback" not in body
        assert "File \"" not in body
