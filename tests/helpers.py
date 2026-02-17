from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


def minimal_graph() -> dict:
    return {
        "id": "root",
        "width": 10,
        "height": 10,
        "children": [],
        "edges": [],
    }


def base_graph() -> dict:
    return {
        "id": "root",
        "width": 220,
        "height": 140,
        "children": [
            {
                "id": "n1",
                "x": 10,
                "y": 20,
                "width": 50,
                "height": 30,
                "type": "router",
                "labels": [
                    {
                        "id": "nl1",
                        "text": "Node 1",
                        "x": 10,
                        "y": 8,
                        "width": 30,
                        "height": 12,
                    }
                ],
                "ports": [
                    {
                        "id": "n1p_w",
                        "x": 0,
                        "y": 12,
                        "width": 4,
                        "height": 4,
                        "labels": [
                            {
                                "id": "pl_w",
                                "text": "west",
                                "x": -14,
                                "y": 0,
                                "width": 12,
                                "height": 4,
                            }
                        ],
                    },
                    {
                        "id": "n1p_e",
                        "x": 46,
                        "y": 12,
                        "width": 4,
                        "height": 4,
                        "labels": [
                            {
                                "id": "pl_e",
                                "text": "east",
                                "x": 6,
                                "y": 0,
                                "width": 12,
                                "height": 4,
                            }
                        ],
                    },
                ],
            },
            {
                "id": "n2",
                "x": 140,
                "y": 20,
                "width": 50,
                "height": 30,
                "labels": [],
                "ports": [
                    {
                        "id": "n2p_w",
                        "x": 0,
                        "y": 12,
                        "width": 4,
                        "height": 4,
                    }
                ],
            },
        ],
        "edges": [
            {
                "id": "e1",
                "sources": ["n1p_e"],
                "targets": ["n2p_w"],
                "layoutOptions": {
                    "org.eclipse.elk.edge.type": "DEPENDENCY",
                    "org.eclipse.elk.edge.thickness": "2",
                },
                "sections": [
                    {
                        "id": "s1",
                        "startPoint": {"x": 60, "y": 34},
                        "bendPoints": [{"x": 100, "y": 34}],
                        "endPoint": {"x": 140, "y": 34},
                    }
                ],
                "junctionPoints": [{"x": 100, "y": 34}],
                "labels": [
                    {
                        "id": "el1",
                        "text": "edge-1",
                        "x": 95,
                        "y": 28,
                        "width": 20,
                        "height": 8,
                    }
                ],
            }
        ],
    }


def graph_with_nested_node() -> dict:
    return {
        "id": "root",
        "width": 300,
        "height": 180,
        "children": [
            {
                "id": "cluster",
                "x": 20,
                "y": 20,
                "width": 200,
                "height": 120,
                "children": [
                    {
                        "id": "inner",
                        "x": 15,
                        "y": 10,
                        "width": 40,
                        "height": 25,
                        "ports": [
                            {
                                "id": "inner-p",
                                "x": 36,
                                "y": 10,
                                "width": 4,
                                "height": 4,
                            }
                        ],
                    }
                ],
                "ports": [],
            }
        ],
        "edges": [],
    }


def deep_copy(data: dict) -> dict:
    return copy.deepcopy(data)


def parse_svg(svg_text: str) -> ET.Element:
    return ET.fromstring(svg_text)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def root_children_signature(root: ET.Element) -> list[tuple[str, str | None]]:
    out: list[tuple[str, str | None]] = []
    for child in list(root):
        out.append((local_name(child.tag), child.get("id")))
    return out


def write_json(path: Path, data: dict) -> None:
    import json

    path.write_text(json.dumps(data), encoding="utf-8")
