from __future__ import annotations

import re

from graphrender import GraphRender

from .helpers import SVG_NS, base_graph, deep_copy, local_name, parse_svg, root_children_signature


def test_root_structure_orders_edges_before_nodes():
    renderer = GraphRender(base_graph(), embed_theme=False)

    root = parse_svg(renderer.to_string())
    children = root_children_signature(root)

    assert children[0] == ("rect", "root")
    assert children[1] == ("defs", None)
    assert children[2] == ("g", "edges")
    assert children[3] == ("g", "nodes")


def test_pretty_output_indents_style_on_new_lines():
    graph = {
        "id": "root",
        "width": 10,
        "height": 10,
        "children": [],
        "edges": [],
    }
    renderer = GraphRender(graph, embed_theme=True, theme_css="a{b:c;}\nq{r:s;}")

    svg_text = renderer.to_string(pretty=True)

    assert "<style>\n" in svg_text
    assert "\n    a{b:c;}\n" in svg_text
    assert "\n    q{r:s;}\n" in svg_text
    assert "\n  </style>" in svg_text


def test_to_string_non_pretty_keeps_compact_output():
    renderer = GraphRender(base_graph(), embed_theme=False)

    pretty = renderer.to_string(pretty=True)
    compact = renderer.to_string(pretty=False)

    assert "\n" in pretty
    assert len(compact) < len(pretty)


def test_node_without_label_uses_node_id_as_fallback_text():
    graph = deep_copy(base_graph())
    graph["children"][1]["labels"] = []

    renderer = GraphRender(graph, embed_theme=False)
    root = parse_svg(renderer.to_string())

    texts = [el.text for el in root.findall(".//svg:g[@id='n2']//svg:text", SVG_NS)]

    assert "n2" in texts


def test_port_label_background_rect_requires_positive_dimensions():
    graph = {
        "id": "root",
        "width": 100,
        "height": 80,
        "children": [
            {
                "id": "n1",
                "x": 10,
                "y": 10,
                "width": 30,
                "height": 20,
                "ports": [
                    {
                        "id": "p1",
                        "x": 0,
                        "y": 8,
                        "width": 4,
                        "height": 4,
                        "labels": [{"id": "l1", "text": "P", "x": -8, "y": 0, "width": 0, "height": 0}],
                    }
                ],
            }
        ],
        "edges": [],
    }
    renderer = GraphRender(graph, embed_theme=False)
    root = parse_svg(renderer.to_string())

    background_rects = root.findall(".//svg:rect[@class='background']", SVG_NS)

    assert len(background_rects) == 1
    assert background_rects[0].get("id") == "root"


def test_edges_group_contains_bend_and_junction_markers():
    renderer = GraphRender(base_graph(), embed_theme=False)
    root = parse_svg(renderer.to_string())

    edge_group = root.find(".//svg:g[@id='e1']", SVG_NS)
    assert edge_group is not None

    circles = [el for el in list(edge_group) if local_name(el.tag) == "circle"]

    assert len(circles) == 2


def test_edge_labels_render_background_and_text():
    renderer = GraphRender(base_graph(), embed_theme=False)
    root = parse_svg(renderer.to_string())

    edge_label_rects = root.findall(
        ".//svg:g[@id='e1']//svg:g[@class='labels']//svg:rect[@class='background']",
        SVG_NS,
    )
    edge_label_texts = root.findall(
        ".//svg:g[@id='e1']//svg:g[@class='labels']//svg:text",
        SVG_NS,
    )

    assert len(edge_label_rects) == 1
    assert [t.text for t in edge_label_texts] == ["edge-1"]


def test_fallback_section_renders_polyline_when_sections_missing():
    graph = deep_copy(base_graph())
    graph["edges"][0].pop("sections", None)

    renderer = GraphRender(graph, embed_theme=False)
    root = parse_svg(renderer.to_string())

    polyline = root.find(".//svg:g[@id='e1']/svg:polyline", SVG_NS)

    assert polyline is not None
    assert polyline.get("points") == "58.0 34.0 142.0 34.0"


def test_icon_defs_and_use_render_with_mocked_fetch(monkeypatch):
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

    icon_svg = "<svg viewBox='0 0 24 24'><path d='M0 0h24v24H0z'/></svg>"
    monkeypatch.setattr(GraphRender, "_fetch_icon_svg", lambda self, name: icon_svg)

    renderer = GraphRender(graph, embed_theme=False)
    root = parse_svg(renderer.to_string())

    defs_icon_groups = root.findall(".//svg:defs/svg:g[@id='icon-mdi-router']", SVG_NS)
    icon_uses = root.findall(".//svg:g[@class='icon']/svg:use", SVG_NS)

    assert len(defs_icon_groups) == 1
    assert len(icon_uses) == 2
    assert all(use.get("href") == "#icon-mdi-router" for use in icon_uses)


def test_canvas_dimensions_follow_padding_and_dimensions():
    renderer = GraphRender(base_graph(), embed_theme=False, padding=5)
    root = parse_svg(renderer.to_string())

    assert root.get("width") == "230"
    assert root.get("height") == "150"


def test_edge_dependency_type_sets_dasharray_and_marker():
    renderer = GraphRender(base_graph(), embed_theme=False)
    root = parse_svg(renderer.to_string())

    polyline = root.find(".//svg:g[@id='e1']/svg:polyline", SVG_NS)

    assert polyline is not None
    assert polyline.get("stroke-dasharray") == "6 3"
    assert polyline.get("marker-end") == "url(#arrow-open)"


def test_style_element_absent_when_embed_theme_disabled():
    renderer = GraphRender(base_graph(), embed_theme=False)
    root = parse_svg(renderer.to_string())

    assert root.find("./svg:style", SVG_NS) is None


def test_style_element_present_when_embed_theme_enabled_with_custom_css():
    renderer = GraphRender(base_graph(), embed_theme=True, theme_css="svg{color:red;}")
    root = parse_svg(renderer.to_string())

    style = root.find("./svg:style", SVG_NS)

    assert style is not None
    assert re.search(r"svg\{color:red;\}", style.text or "")
