from __future__ import annotations

import json

import pytest

from graphrender import GraphRender

from .helpers import base_graph, deep_copy, graph_with_nested_node, minimal_graph, write_json


def test_from_json_and_from_file_collect_expected_items(tmp_path):
    graph = base_graph()
    json_path = tmp_path / "graph.json"
    write_json(json_path, graph)

    from_json = GraphRender.from_json(json.dumps(graph), embed_theme=False)
    from_file = GraphRender.from_file(json_path, embed_theme=False)

    assert len(from_json.nodes) == len(from_file.nodes) == 2
    assert len(from_json.edges) == len(from_file.edges) == 1
    assert len(from_json.labels) == len(from_file.labels) == 4


def test_collect_graph_resolves_nested_absolute_coordinates():
    renderer = GraphRender(graph_with_nested_node(), embed_theme=False)

    inner = next(node for node in renderer.nodes if node["id"] == "inner")
    assert inner["x"] == 35
    assert inner["y"] == 30

    port = renderer.port_lookup["inner-p"]
    assert port["x"] == 71
    assert port["y"] == 40


def test_option_value_prefers_layout_options_over_properties():
    renderer = GraphRender(minimal_graph(), embed_theme=False)
    item = {
        "layoutOptions": {"key": "layout"},
        "properties": {"key": "properties"},
    }

    assert renderer._option_value(item, "key") == "layout"


def test_font_size_parses_and_rejects_invalid_values():
    renderer = GraphRender(minimal_graph(), embed_theme=False)

    assert renderer._font_size({"layoutOptions": {"org.eclipse.elk.font.size": "10.5"}}) == 10.5
    assert renderer._font_size({"properties": {"org.eclipse.elk.font.size": "11"}}) == 11.0
    assert renderer._font_size({"layoutOptions": {"org.eclipse.elk.font.size": "not-a-number"}}) is None


def test_partition_labels_groups_explicit_owner_kinds():
    renderer = GraphRender(base_graph(), embed_theme=False)

    grouped = renderer._partition_labels()

    assert "n1" in grouped["node"]
    assert "n1p_w" in grouped["port"]
    assert "e1" in grouped["edge"]


def test_partition_labels_prefers_edge_when_owner_id_overlaps():
    renderer = GraphRender(minimal_graph(), embed_theme=False)
    renderer.node_lookup["shared"] = {"id": "shared"}
    renderer.port_lookup["shared"] = {"id": "shared", "side": "WEST", "x": 0, "y": 0, "width": 1, "height": 1}
    renderer.edges = [{"edge": {"id": "shared"}, "offset": (0, 0)}]
    renderer.labels = [
        {
            "owner": "shared",
            "text": "ambiguous",
            "x": 1,
            "y": 1,
            "width": 0,
            "height": 0,
        }
    ]

    grouped = renderer._partition_labels()

    assert grouped["edge"]["shared"][0]["text"] == "ambiguous"
    assert "shared" not in grouped["node"]
    assert "shared" not in grouped["port"]


def test_label_text_anchor_is_side_aware_for_ports():
    renderer = GraphRender(base_graph(), embed_theme=False)

    assert renderer.port_lookup["n1p_w"]["side"] == "WEST"
    assert renderer.port_lookup["n1p_e"]["side"] == "EAST"
    assert renderer._label_text_anchor("n1p_w", owner_kind="port") == "end"
    assert renderer._label_text_anchor("n1p_e", owner_kind="port") == "start"
    assert renderer._label_text_anchor("unknown", owner_kind="port") == "middle"


def test_label_to_text_uses_port_baseline_for_relative_position():
    renderer = GraphRender(base_graph(), embed_theme=False)

    above = renderer._label_to_text(
        {"owner": "n1p_w", "text": "A", "x": 0, "y": 25, "width": 0, "height": 0},
        owner_kind="port",
    )
    below = renderer._label_to_text(
        {"owner": "n1p_w", "text": "B", "x": 0, "y": 40, "width": 0, "height": 0},
        owner_kind="port",
    )

    assert above.dominant_baseline == "text-before-edge"
    assert below.dominant_baseline == "text-after-edge"


def test_edge_thickness_normalizes_non_positive_and_invalid_values():
    renderer = GraphRender(minimal_graph(), embed_theme=False)

    assert renderer._edge_thickness({"layoutOptions": {"org.eclipse.elk.edge.thickness": "0"}}) == 1.0
    assert renderer._edge_thickness({"layoutOptions": {"org.eclipse.elk.edge.thickness": -5}}) == 1.0
    assert renderer._edge_thickness({"layoutOptions": {"org.eclipse.elk.edge.thickness": "2.5"}}) == 2.5
    assert renderer._edge_thickness({"layoutOptions": {"org.eclipse.elk.edge.thickness": "bad"}}) is None


@pytest.mark.parametrize(
    "edge_type,expected_end,expected_dash",
    [
        ("NONE", None, None),
        ("UNDIRECTED", None, None),
        ("DIRECTED", "url(#arrow)", None),
        ("ASSOCIATION", "url(#arrow-open)", None),
        ("DEPENDENCY", "url(#arrow-open)", "6 3"),
        ("GENERALIZATION", "url(#triangle-hollow)", None),
    ],
)
def test_edge_rendering_maps_type_to_markers(edge_type, expected_end, expected_dash):
    renderer = GraphRender(minimal_graph(), embed_theme=False)
    edge = {"layoutOptions": {"org.eclipse.elk.edge.type": edge_type}}

    render = renderer._edge_rendering(edge)

    assert render["marker_end"] == expected_end
    assert render["stroke_dasharray"] == expected_dash


def test_fallback_section_uses_source_and_target_port_centers():
    graph = deep_copy(base_graph())
    graph["edges"][0].pop("sections", None)
    renderer = GraphRender(graph, embed_theme=False)
    entry = renderer.edges[0]

    fallback = renderer._fallback_section(entry["edge"], entry["offset"])

    assert fallback == {
        "startPoint": {"x": 58.0, "y": 34.0},
        "endPoint": {"x": 142.0, "y": 34.0},
        "bendPoints": [],
    }


def test_canvas_size_falls_back_to_node_extents_when_missing_dimensions():
    graph = deep_copy(base_graph())
    graph.pop("width")
    graph.pop("height")

    renderer = GraphRender(graph, embed_theme=False, padding=3)

    assert renderer._canvas_size() == (196, 56)


def test_port_label_without_coordinates_defaults_to_port_center():
    graph = {
        "id": "root",
        "width": 100,
        "height": 80,
        "children": [
            {
                "id": "node",
                "x": 10,
                "y": 10,
                "width": 30,
                "height": 20,
                "ports": [
                    {
                        "id": "port",
                        "x": 26,
                        "y": 8,
                        "width": 4,
                        "height": 4,
                        "labels": [{"id": "pl", "text": "label", "width": 8, "height": 4}],
                    }
                ],
            }
        ],
        "edges": [],
    }
    renderer = GraphRender(graph, embed_theme=False)

    port_label = next(lbl for lbl in renderer.labels if lbl["owner"] == "port")

    assert port_label["x"] == 38.0
    assert port_label["y"] == 20.0
