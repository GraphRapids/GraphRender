from __future__ import annotations

from graphrender import default_theme_css


def test_default_theme_css_returns_non_empty_stylesheet():
    css = default_theme_css()

    assert css
    assert ":root" in css
    assert "#nodes .node > rect" in css
