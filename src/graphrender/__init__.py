"""
GraphRender package initialization.
Exports the ElkGraphSvg converter and resource helpers.
"""

from .elk_graph_svg import ElkGraphSvg

from .resources import default_theme_css

__all__ = [
    "ElkGraphSvg",
    "default_theme_css",
]
