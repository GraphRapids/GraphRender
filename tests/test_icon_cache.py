from __future__ import annotations

from pathlib import Path
from urllib.error import URLError

import graphrender.graphrender as renderer_module
from graphrender import GraphRender

from .helpers import minimal_graph


class FakeResponse:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self.payload.encode("utf-8")


def test_resolve_cache_dir_uses_explicit_env_override(monkeypatch, tmp_path):
    cache_dir = tmp_path / "icons"
    monkeypatch.setenv("GRAPHRENDER_ICON_CACHE_DIR", str(cache_dir))

    renderer = GraphRender(minimal_graph(), embed_theme=False)

    assert renderer._icon_cache_dir == cache_dir


def test_resolve_cache_dir_empty_env_disables_disk_cache(monkeypatch):
    monkeypatch.setenv("GRAPHRENDER_ICON_CACHE_DIR", "")

    renderer = GraphRender(minimal_graph(), embed_theme=False)

    assert renderer._icon_cache_dir is None
    assert renderer._icon_cache_path("mdi:router") is None


def test_resolve_cache_dir_prefers_xdg(monkeypatch, tmp_path):
    monkeypatch.delenv("GRAPHRENDER_ICON_CACHE_DIR", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    renderer = GraphRender(minimal_graph(), embed_theme=False)

    assert renderer._icon_cache_dir == tmp_path / "xdg" / "graphrender" / "icons"


def test_resolve_cache_dir_uses_localappdata_when_xdg_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("GRAPHRENDER_ICON_CACHE_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localapp"))

    renderer = GraphRender(minimal_graph(), embed_theme=False)

    assert renderer._icon_cache_dir == tmp_path / "localapp" / "graphrender" / "icons"


def test_resolve_cache_dir_falls_back_to_home(monkeypatch, tmp_path):
    monkeypatch.delenv("GRAPHRENDER_ICON_CACHE_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    renderer = GraphRender(minimal_graph(), embed_theme=False)

    assert renderer._icon_cache_dir == Path(tmp_path / "home" / ".cache" / "graphrender" / "icons")


def test_icon_cache_path_sanitizes_icon_name(monkeypatch, tmp_path):
    monkeypatch.setenv("GRAPHRENDER_ICON_CACHE_DIR", str(tmp_path / "cache"))
    renderer = GraphRender(minimal_graph(), embed_theme=False)

    path = renderer._icon_cache_path("mdi:router?outline")

    assert path is not None
    assert path.name.startswith("mdi-router-outline-")
    assert path.name.endswith(".svg")


def test_store_and_load_icon_svg_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("GRAPHRENDER_ICON_CACHE_DIR", str(tmp_path / "cache"))
    renderer = GraphRender(minimal_graph(), embed_theme=False)
    icon_name = "mdi:router"
    svg_text = "<svg viewBox='0 0 24 24'></svg>"

    renderer._store_icon_svg_to_disk(icon_name, svg_text)

    loaded = renderer._load_icon_svg_from_disk(icon_name)

    assert loaded == svg_text


def test_fetch_icon_svg_uses_valid_disk_cache_without_network(monkeypatch, tmp_path):
    monkeypatch.setenv("GRAPHRENDER_ICON_CACHE_DIR", str(tmp_path / "cache"))
    renderer = GraphRender(minimal_graph(), embed_theme=False)
    icon_name = "mdi:router"
    valid_svg = "<svg viewBox='0 0 24 24'><path d='M0 0h24v24H0z'/></svg>"

    cache_path = renderer._icon_cache_path(icon_name)
    assert cache_path is not None
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(valid_svg, encoding="utf-8")

    monkeypatch.setattr(renderer_module, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network should not be used")))

    assert renderer._fetch_icon_svg(icon_name) == valid_svg


def test_fetch_icon_svg_auto_heals_malformed_disk_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("GRAPHRENDER_ICON_CACHE_DIR", str(tmp_path / "cache"))
    renderer = GraphRender(minimal_graph(), embed_theme=False)
    icon_name = "mdi:router"
    good_svg = "<svg viewBox='0 0 24 24'><path d='M0 0h24v24H0z'/></svg>"

    cache_path = renderer._icon_cache_path(icon_name)
    assert cache_path is not None
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("not-an-svg", encoding="utf-8")

    monkeypatch.setattr(renderer_module, "urlopen", lambda *args, **kwargs: FakeResponse(good_svg))

    fetched = renderer._fetch_icon_svg(icon_name)

    assert fetched == good_svg
    assert cache_path.read_text(encoding="utf-8") == good_svg


def test_fetch_icon_svg_network_errors_cached_as_none(monkeypatch, tmp_path):
    calls = {"count": 0}
    monkeypatch.setenv("GRAPHRENDER_ICON_CACHE_DIR", str(tmp_path / "cache"))

    def raising(*args, **kwargs):
        calls["count"] += 1
        raise URLError("offline")

    monkeypatch.setattr(renderer_module, "urlopen", raising)
    renderer = GraphRender(minimal_graph(), embed_theme=False)

    assert renderer._fetch_icon_svg("mdi:router") is None
    assert renderer._fetch_icon_svg("mdi:router") is None
    assert calls["count"] == 1


def test_icon_geometry_parses_viewbox_and_caches(monkeypatch):
    calls = {"count": 0}

    def fake_fetch(self, icon_name):
        calls["count"] += 1
        return "<svg viewBox='0 0 24 12'><path d='M0 0h24v12H0z'/></svg>"

    monkeypatch.setattr(GraphRender, "_fetch_icon_svg", fake_fetch)
    renderer = GraphRender(minimal_graph(), embed_theme=False)

    first = renderer._icon_geometry("mdi:router")
    second = renderer._icon_geometry("mdi:router")

    assert first == ("<path d=\"M0 0h24v12H0z\" />", 24.0, 12.0)
    assert second == first
    assert calls["count"] == 1


def test_icon_geometry_falls_back_to_width_height(monkeypatch):
    monkeypatch.setattr(
        GraphRender,
        "_fetch_icon_svg",
        lambda self, icon_name: "<svg width='16px' height='8px'><path d='M0 0h16v8H0z'/></svg>",
    )
    renderer = GraphRender(minimal_graph(), embed_theme=False)

    geom = renderer._icon_geometry("mdi:router")

    assert geom == ("<path d=\"M0 0h16v8H0z\" />", 16.0, 8.0)


def test_icon_geometry_rejects_invalid_dimensions(monkeypatch):
    monkeypatch.setattr(
        GraphRender,
        "_fetch_icon_svg",
        lambda self, icon_name: "<svg width='0' height='0'><path d=''/></svg>",
    )
    renderer = GraphRender(minimal_graph(), embed_theme=False)

    assert renderer._icon_geometry("mdi:router") is None


def test_build_icon_defs_deduplicates_identical_icons(monkeypatch):
    graph = {
        "id": "root",
        "width": 80,
        "height": 60,
        "children": [
            {"id": "n1", "x": 10, "y": 10, "width": 24, "height": 24, "icon": "mdi:router"},
            {"id": "n2", "x": 40, "y": 10, "width": 24, "height": 24, "icon": "mdi:router"},
        ],
        "edges": [],
    }

    monkeypatch.setattr(GraphRender, "_icon_geometry", lambda self, icon_name: ("<path d='M0 0h1v1H0z'/>", 1.0, 1.0))

    renderer = GraphRender(graph, embed_theme=False)
    defs = renderer._build_icon_defs()

    assert len(defs) == 1
    assert renderer._icon_def_id("mdi:router") == "icon-mdi-router"
