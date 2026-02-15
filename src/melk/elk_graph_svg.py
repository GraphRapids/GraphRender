"""
Generate SVGs from Eclipse Layout Kernel (ELK) JSON output using svg.py.

This module converts an ELK layout graph (the JSON that ELK emits after
running a layout algorithm) into a styled SVG that includes:
- nodes (rectangles by default)
- ports
- node, edge and port labels
- edges with bend points and junction points
- support for nested / compound graphs (coordinates are resolved recursively)
"""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from .resources import default_theme_css

import svg

Number = float | int
Point = Tuple[Number, Number]

ET.register_namespace("", "http://www.w3.org/2000/svg")


class ElkGraphSvg:
    """Convert ELK JSON to svg.py structures."""

    def __init__(
        self,
        graph: Dict,
        *,
        padding: Number = 0,
        node_style: Optional[Dict] = None,
        port_style: Optional[Dict] = None,
        edge_style: Optional[Dict] = None,
        font_size: Number = 12,
        embed_theme: bool = True,
        theme_css: Optional[str] = None,
    ) -> None:
        self.graph = graph
        self.padding = padding
        self.font_size = font_size
        self.embed_theme = embed_theme
        self.theme_css = theme_css

        self.node_style = {
            "fill": "lightblue",
            "stroke": "black",
            "rx": 2,
        }
        if node_style:
            self.node_style.update(node_style)

        self.port_style = {
            "fill": "#444",
            "stroke": "#111",
        }
        if port_style:
            self.port_style.update(port_style)

        self.edge_style = {
            "stroke": "#222",
            "stroke_width": 1.5,
        }
        if edge_style:
            self.edge_style.update(edge_style)

        # Internal collections filled by _collect_graph.
        self.nodes: List[Dict] = []
        self.edges: List[Dict] = []
        self.labels: List[Dict] = []
        self.port_lookup: Dict[str, Dict] = {}
        self.node_lookup: Dict[str, Dict] = {}
        self._icon_cache: Dict[str, Optional[str]] = {}
        self._icon_geom_cache: Dict[str, Optional[Tuple[str, float, float]]] = {}
        self._icon_def_ids: Dict[str, str] = {}
        self._defs_cache: Optional[svg.Defs] = None

        self._collect_graph(self.graph, offset=(0, 0))

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _option_value(self, item: Dict, *keys: str) -> Optional[object]:
        """Read an ELK option from layoutOptions/properties with stable precedence."""
        opts = item.get("layoutOptions") or {}
        props = item.get("properties") or {}
        for key in keys:
            if key in opts:
                return opts[key]
            if key in props:
                return props[key]
        return None

    def _font_size(self, item: Dict) -> Optional[Number]:
        """Extract an optional font size from ELK options/properties."""
        value = self._option_value(
            item,
            "org.eclipse.elk.font.size",
            "elk.font.size",
            "font.size",
        )
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _port_side(self, port: Dict) -> Optional[str]:
        """Return the port side (WEST/EAST/NORTH/SOUTH) if present."""
        val = self._option_value(
            port,
            "org.eclipse.elk.port.side",
            "elk.port.side",
            "port.side",
        )
        if isinstance(val, str):
            return val.upper()
        return None

    def _label_text_anchor(self, owner: Optional[str]) -> str:
        """Determine text-anchor based on owner type (ports care about side)."""
        if owner and owner in self.port_lookup:
            side = self.port_lookup[owner].get("side")
            if side == "WEST":
                return "end"
            if side == "EAST":
                return "start"
        return "middle"

    def _partition_labels(self) -> Dict[str, Dict[str, List[Dict]]]:
        """Group labels by their owner type for structured rendering."""
        node_labels: Dict[str, List[Dict]] = {}
        port_labels: Dict[str, List[Dict]] = {}
        edge_labels: Dict[str, List[Dict]] = {}

        for lbl in self.labels:
            owner = lbl.get("owner")
            if owner in self.port_lookup:
                port_labels.setdefault(owner, []).append(lbl)
            elif owner in self.node_lookup:
                node_labels.setdefault(owner, []).append(lbl)
            else:
                edge_labels.setdefault(owner or "", []).append(lbl)

        return {
            "node": node_labels,
            "port": port_labels,
            "edge": edge_labels,
        }

    def _edge_thickness(self, edge: Dict) -> Optional[Number]:
        """Extract an optional stroke width for an edge."""
        value = self._option_value(
            edge,
            "org.eclipse.elk.edge.thickness",
            "elk.edge.thickness",
            "edge.thickness",
            "stroke.width",
        )
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _edge_type(self, edge: Dict) -> Optional[str]:
        """Return the edge type when set directly on the edge object."""
        val = edge.get("type")
        return str(val) if val is not None else None

    # ------------------------------------------------------------------ #
    # Icons
    # ------------------------------------------------------------------ #
    def _fetch_icon_svg(self, icon_name: str) -> Optional[str]:
        """Download an Iconify SVG once and memoize the string."""
        if icon_name in self._icon_cache:
            return self._icon_cache[icon_name]

        url = f"https://api.iconify.design/{icon_name}.svg"
        try:
            req = Request(url, headers={"User-Agent": "melk/1.0"})
            with urlopen(req, timeout=5) as resp:  # type: ignore[arg-type]
                data = resp.read().decode("utf-8")
                self._icon_cache[icon_name] = data
                return data
        except (HTTPError, URLError, TimeoutError, ValueError):
            self._icon_cache[icon_name] = None
            return None

    def _icon_def_id(self, icon_name: str) -> str:
        """Return a stable, sanitized id for an icon definition."""
        existing = self._icon_def_ids.get(icon_name)
        if existing:
            return existing

        safe = re.sub(r"[^a-zA-Z0-9_-]", "-", icon_name).strip("-_")
        if not safe:
            safe = "icon"
        candidate = f"icon-{safe}"
        if candidate in self._icon_def_ids.values():
            suffix = hashlib.sha1(icon_name.encode("utf-8")).hexdigest()[:8]
            candidate = f"{candidate}-{suffix}"

        self._icon_def_ids[icon_name] = candidate
        return candidate

    def _icon_geometry(self, icon_name: str) -> Optional[Tuple[str, float, float]]:
        """Return (inner_svg, width, height) for an icon, cached by name."""
        if icon_name in self._icon_geom_cache:
            return self._icon_geom_cache[icon_name]

        svg_text = self._fetch_icon_svg(icon_name)
        if not svg_text:
            self._icon_geom_cache[icon_name] = None
            return None
        try:
            root = ET.fromstring(svg_text)
        except ET.ParseError:
            self._icon_geom_cache[icon_name] = None
            return None

        view_box = root.get("viewBox")
        vb_w = vb_h = None
        if view_box:
            parts = view_box.split()
            if len(parts) == 4:
                try:
                    vb_w, vb_h = float(parts[2]), float(parts[3])
                except ValueError:
                    vb_w = vb_h = None

        if vb_w is None or vb_h is None:
            try:
                vb_w = float((root.get("width") or "0").replace("px", ""))
                vb_h = float((root.get("height") or "0").replace("px", ""))
            except ValueError:
                self._icon_geom_cache[icon_name] = None
                return None

        if vb_w <= 0 or vb_h <= 0:
            self._icon_geom_cache[icon_name] = None
            return None

        inner = "".join(ET.tostring(child, encoding="unicode") for child in list(root))
        cached = (inner, vb_w, vb_h)
        self._icon_geom_cache[icon_name] = cached
        return cached

    def _raw_element(self, text: str):
        """Return a svg.Raw (or inline fallback) for a raw SVG fragment."""
        raw_cls = getattr(svg, "Raw", None)
        if raw_cls:
            try:
                return raw_cls(text)
            except Exception:
                pass

        class _InlineRaw:
            def __init__(self, raw_text: str) -> None:
                self.text = raw_text

            def as_str(self) -> str:
                return self.text

            def __str__(self) -> str:
                return self.text

        return _InlineRaw(text)

    def _icon_element(self, icon_name: str, node: Dict):
        """
        Return a scaled svg.Raw (or fallback object) that centers the icon
        within the node rectangle. Parsing and viewBox extraction are cached
        per icon to avoid repeated XML parsing.
        """
        cached = self._icon_geometry(icon_name)
        if cached is None:
            return None

        _, vb_w, vb_h = cached

        margin = 4
        target_w = max(node["width"] - margin * 2, 1)
        target_h = max(node["height"] - margin * 2, 1)
        scale = min(target_w / vb_w, target_h / vb_h)

        cx = node["x"] + node["width"] / 2
        cy = node["y"] + node["height"] / 2

        icon_id = self._icon_def_id(icon_name)
        g_str = (
            f'<g class="icon" transform="translate({cx},{cy}) '
            f'scale({scale}) translate({-vb_w/2},{-vb_h/2})">'
            f'<use href="#{icon_id}"/></g>'
        )

        return self._raw_element(g_str)

    def _label_to_text(self, lbl: Dict) -> svg.Text:
        """Create an svg.Text element for a label dict."""
        x = lbl["x"] + lbl.get("width", 0) / 2
        y = lbl["y"] + lbl.get("height", 0) / 2
        lbl_font_size = lbl.get("font_size") or self.font_size
        text_anchor = self._label_text_anchor(lbl.get("owner"))
        dominant_baseline = "middle"
        owner = lbl.get("owner")
        if owner and owner in self.port_lookup:
            side = self.port_lookup[owner].get("side")
            if side == "SOUTH":
                dominant_baseline = "text-top"
            elif side == "NORTH":
                dominant_baseline = "hanging"
        return svg.Text(
            text=lbl.get("text", ""),
            x=x,
            y=y,
            font_size=lbl_font_size,
            text_anchor=text_anchor,
            dominant_baseline=dominant_baseline,
            fill="#111",
        )

    # ------------------------------------------------------------------ #
    # Constructors
    # ------------------------------------------------------------------ #
    @classmethod
    def from_file(cls, path: str | Path, **kwargs) -> "ElkGraphSvg":
        """Load ELK JSON from a file."""
        data = json.loads(Path(path).read_text())
        return cls(data, **kwargs)

    @classmethod
    def from_json(cls, json_str: str, **kwargs) -> "ElkGraphSvg":
        """Load ELK JSON from a JSON string."""
        data = json.loads(json_str)
        return cls(data, **kwargs)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def to_svg_element(self) -> svg.SVG:
        """Return the root svg.SVG element."""
        width, height = self._canvas_size()

        root = svg.SVG(width=width, height=height, elements=[])

        bg_rect = self._build_background_rect(width, height)
        if bg_rect:
            root.elements.append(bg_rect)

        style_el = self._build_style_element()
        if style_el:
            root.elements.append(style_el)

        root.elements.append(self._build_defs())

        label_maps = self._partition_labels()

        nodes_group = self._build_nodes_group(label_maps)
        if nodes_group is not None:
            root.elements.append(nodes_group)

        edges_group = self._build_edges_group(label_maps)
        if edges_group is not None:
            root.elements.append(edges_group)

        return root

    def _build_style_element(self):
        """Optionally build a <style> element from the bundled theme."""
        if not self.embed_theme:
            return None

        css_text = self.theme_css if self.theme_css is not None else default_theme_css()
        if not css_text:
            return None

        style_cls = getattr(svg, "Style", None)
        if style_cls:
            try:
                return style_cls(content=css_text)
            except Exception:
                pass

        raw_cls = getattr(svg, "Raw", None)
        if raw_cls:
            try:
                return raw_cls(f"<style>{css_text}</style>")
            except Exception:
                pass

        class _InlineStyle:
            def __init__(self, css: str) -> None:
                self.css = css

            def as_str(self) -> str:
                return f"<style>{self.css}</style>"

            def __str__(self) -> str:  # svg.py may fall back to str()
                return self.as_str()

        return _InlineStyle(css_text)

    def to_string(self) -> str:
        """Return the SVG as a string."""
        return self.to_svg_element().as_str()

    def write(self, path: str | Path) -> None:
        """Write the SVG to disk."""
        Path(path).write_text(self.to_string())

    # ------------------------------------------------------------------ #
    # Graph collection
    # ------------------------------------------------------------------ #
    def _collect_graph(self, graph: Dict, offset: Point) -> None:
        """
        Traverse the ELK graph recursively and accumulate:
        - nodes (absolute coordinates)
        - ports (absolute coordinates)
        - labels (node + edge)
        - edges (with the offset of their containing graph)

        ELK coordinates are relative to the containing graph. We normalize
        everything into the root coordinate system by carrying an `offset`
        down the recursion.
        """
        base_x = offset[0] + graph.get("x", 0)
        base_y = offset[1] + graph.get("y", 0)
        base_offset = (base_x, base_y)

        for node in graph.get("children", []):
            abs_x = base_offset[0] + node.get("x", 0)
            abs_y = base_offset[1] + node.get("y", 0)
            record = {
                "id": node["id"],
                "x": abs_x,
                "y": abs_y,
                "width": node.get("width", 0),
                "height": node.get("height", 0),
                "raw": node,
            }
            self.nodes.append(record)
            self.node_lookup[record["id"]] = record

            # Node labels (coordinates relative to the node).
            for label in node.get("labels", []):
                self.labels.append(
                    {
                        "owner": node["id"],
                        "id": label.get("id"),
                        "text": label.get("text", ""),
                        "x": abs_x + label.get("x", 0),
                        "y": abs_y + label.get("y", 0),
                        "width": label.get("width", 0),
                        "height": label.get("height", 0),
                        "font_size": self._font_size(label),
                    }
                )

            # Ports (coordinates relative to the node).
            for port in node.get("ports", []):
                port_abs = {
                    "id": port["id"],
                    "owner": node["id"],
                    "x": abs_x + port.get("x", 0),
                    "y": abs_y + port.get("y", 0),
                    "width": port.get("width", 0),
                    "height": port.get("height", 0),
                    "raw": port,
                    "side": self._port_side(port),
                }
                self.port_lookup[port_abs["id"]] = port_abs

                # Port labels (coordinates relative to the port). If ELK didn't
                # emit coordinates, place the label at the port center.
                for label in port.get("labels", []) or []:
                    lx = label.get("x")
                    ly = label.get("y")
                    if lx is None or ly is None:
                        lx = port_abs["x"] + port_abs.get("width", 0) / 2
                        ly = port_abs["y"] + port_abs.get("height", 0) / 2
                    else:
                        lx = port_abs["x"] + lx
                        ly = port_abs["y"] + ly

                    self.labels.append(
                        {
                            "owner": port["id"],
                            "id": label.get("id"),
                            "text": label.get("text", ""),
                            "x": lx,
                            "y": ly,
                            "width": label.get("width", 0),
                            "height": label.get("height", 0),
                            "font_size": self._font_size(label),
                        }
                    )

            # Recurse into nested graphs.
            self._collect_graph(node, base_offset)

        # Edge labels are stored alongside the edge.
        for edge in graph.get("edges", []):
            self.edges.append({"edge": edge, "offset": base_offset})
            for label in edge.get("labels", []):
                self.labels.append(
                    {
                        "owner": edge["id"],
                        "id": label.get("id"),
                        "text": label.get("text", ""),
                        "x": base_offset[0] + label.get("x", 0),
                        "y": base_offset[1] + label.get("y", 0),
                        "width": label.get("width", 0),
                        "height": label.get("height", 0),
                        "font_size": self._font_size(label),
                    }
                )

    # ------------------------------------------------------------------ #
    # Drawing helpers
    # ------------------------------------------------------------------ #
    def _build_defs(self) -> svg.Defs:
        """Marker definitions (arrow heads, etc.). Memoized per instance."""
        if self._defs_cache is not None:
            return self._defs_cache

        arrow = svg.Marker(
            id="arrow",
            markerWidth=10,
            markerHeight=10,
            refX=5,
            refY=5,
            orient="auto",
            markerUnits="strokeWidth",
            elements=[
                svg.Path(
                    d=[
                        svg.MoveTo(0, 0),
                        svg.LineTo(10, 5),
                        svg.LineTo(0, 10),
                        svg.LineTo(2, 5),
                        svg.Z(),
                    ],
                    fill=self.edge_style["stroke"],
                )
            ],
        )

        open_arrow = svg.Marker(
            id="arrow-open",
            markerWidth=10,
            markerHeight=10,
            refX=10,
            refY=5,
            orient="auto",
            markerUnits="strokeWidth",
            elements=[
                svg.Path(
                    d=[svg.MoveTo(0, 0), svg.LineTo(10, 5), svg.LineTo(0, 10)],
                    fill="none",
                    stroke=self.edge_style["stroke"],
                    stroke_width=self.edge_style["stroke_width"],
                )
            ],
        )

        triangle_hollow = svg.Marker(
            id="triangle-hollow",
            markerWidth=12,
            markerHeight=12,
            refX=10,
            refY=6,
            orient="auto",
            markerUnits="strokeWidth",
            elements=[
                svg.Path(
                    d=[
                        svg.MoveTo(0, 0),
                        svg.LineTo(10, 6),
                        svg.LineTo(0, 12),
                        svg.Z(),
                    ],
                    fill="white",
                    stroke=self.edge_style["stroke"],
                    stroke_width=self.edge_style["stroke_width"],
                )
            ],
        )

        elements = [arrow, open_arrow, triangle_hollow]
        elements.extend(self._build_icon_defs())
        self._defs_cache = svg.Defs(elements=elements)
        return self._defs_cache

    def _build_icon_defs(self) -> List[object]:
        """Define icon glyphs once in <defs> for reuse via <use>."""
        icon_defs: List[object] = []
        seen: set[str] = set()

        for node in self.nodes:
            icon_name = node["raw"].get("icon")
            if not icon_name:
                continue
            icon_name = str(icon_name)
            if icon_name in seen:
                continue
            seen.add(icon_name)

            geom = self._icon_geometry(icon_name)
            if not geom:
                continue
            inner, _, _ = geom
            icon_id = self._icon_def_id(icon_name)
            icon_defs.append(self._raw_element(f'<g id="{icon_id}">{inner}</g>'))

        return icon_defs

    def _build_background_rect(self, canvas_width: Number, canvas_height: Number):
        """Optional background rect covering the root graph area."""
        try:
            width = canvas_width - self.padding * 2
            height = canvas_height - self.padding * 2
            if width <= 0 or height <= 0:
                return None
            return svg.Rect(
                id=self.graph.get("id"),
                class_="background",
                x=self.padding,
                y=self.padding,
                width=width,
                height=height,
                fill="none",
                stroke="none",
            )
        except Exception:
            return None

    def _build_nodes_group(self, label_maps: Dict[str, Dict[str, List[Dict]]]) -> Optional[svg.G]:
        """Create the nodes group with nested ports and labels."""
        owners_with_labels = {lbl["owner"] for lbl in self.labels if lbl.get("text")}
        nodes_root = svg.G(id="nodes", elements=[])

        node_label_map = label_maps["node"]
        port_label_map = label_maps["port"]

        for node in self.nodes:
            node_classes = ["node"]
            node_type = node["raw"].get("type")
            if node_type:
                node_classes.append(str(node_type))

            node_group = svg.G(
                id=node["id"], class_=" ".join(node_classes), elements=[]
            )

            # Node shape
            rect = svg.Rect(
                x=node["x"],
                y=node["y"],
                width=node["width"],
                height=node["height"],
                fill=self.node_style["fill"],
                stroke=self.node_style["stroke"],
                rx=self.node_style.get("rx"),
            )
            node_group.elements.append(rect)

            # Centered icon (if provided via node["raw"]["icon"]).
            icon_name = node["raw"].get("icon")
            if icon_name:
                icon_el = self._icon_element(str(icon_name), node)
                if icon_el:
                    node_group.elements.append(icon_el)

            # Node labels
            node_labels_g = svg.G(class_="labels", elements=[])
            for lbl in node_label_map.get(node["id"], []):
                node_labels_g.elements.append(self._label_to_text(lbl))
            if not node_labels_g.elements and node["id"] not in owners_with_labels:
                center_x = node["x"] + node["width"] / 2
                center_y = node["y"] + node["height"] / 2
                node_labels_g.elements.append(
                    svg.Text(
                        text=node["id"],
                        x=center_x,
                        y=center_y,
                        font_size=self.font_size,
                        text_anchor="middle",
                        dominant_baseline="middle",
                        fill="#111",
                    )
                )
            node_group.elements.append(node_labels_g)

            # Ports
            ports_g = svg.G(class_="ports", elements=[])
            for port in (node["raw"].get("ports") or []):
                port_abs = self.port_lookup[port["id"]]
                port_g = svg.G(id=port["id"], class_="port", elements=[])
                port_rect = svg.Rect(
                    x=port_abs["x"],
                    y=port_abs["y"],
                    width=port_abs.get("width", 0),
                    height=port_abs.get("height", 0),
                    fill=self.port_style["fill"],
                    stroke=self.port_style["stroke"],
                )
                port_g.elements.append(port_rect)

                port_labels_g = svg.G(class_="labels", elements=[])
                for lbl in port_label_map.get(port["id"], []):
                    port_labels_g.elements.append(self._label_to_text(lbl))
                if port_labels_g.elements:
                    port_g.elements.append(port_labels_g)

                ports_g.elements.append(port_g)

            if ports_g.elements:
                node_group.elements.append(ports_g)

            nodes_root.elements.append(node_group)

        if not nodes_root.elements:
            return None

        return nodes_root

    def _build_edges_group(self, label_maps: Dict[str, Dict[str, List[Dict]]]) -> Optional[svg.G]:
        """Create edges group with per-edge subgroups and labels."""
        edge_labels = label_maps["edge"]
        edges_root = svg.G(id="edges", elements=[])

        for entry in self.edges:
            edge = entry["edge"]
            offset = entry["offset"]
            edge_classes = ["edge"]
            etype = self._edge_type(edge)
            if etype:
                edge_classes.append(str(etype))

            edge_group = svg.G(id=edge.get("id"), class_=" ".join(edge_classes), elements=[])
            edge_thickness = self._edge_thickness(edge) or self.edge_style["stroke_width"]

            sections = edge.get("sections") or []
            if not sections:
                fallback = self._fallback_section(edge, offset)
                if fallback:
                    sections = [fallback]

            for section in sections:
                points = self._section_points(edge, section, offset)
                if not points:
                    continue
                render = self._edge_rendering(edge)
                poly_kwargs = {
                    "points": [coord for pt in points for coord in pt],
                    "stroke": self.edge_style["stroke"],
                    "fill": "none",
                    "stroke_width": edge_thickness,
                }
                if render["marker_end"]:
                    poly_kwargs["marker_end"] = render["marker_end"]
                if render["marker_start"]:
                    poly_kwargs["marker_start"] = render["marker_start"]
                if render["stroke_dasharray"]:
                    poly_kwargs["stroke_dasharray"] = render["stroke_dasharray"]

                polyline = svg.Polyline(**poly_kwargs)
                edge_group.elements.append(polyline)

                # Bend points for visibility/debugging.
                for bend in section.get("bendPoints", []) or []:
                    bx, by = self._apply_offset(bend, offset)
                    edge_group.elements.append(
                        svg.Circle(cx=bx, cy=by, r=2, fill="#888", stroke="none")
                    )

            # Junction points.
            for jp in edge.get("junctionPoints", []) or []:
                jx, jy = self._apply_offset(jp, offset)
                edge_group.elements.append(svg.Circle(cx=jx, cy=jy, r=2.5, fill="#444"))

            # Edge labels
            labels_g = svg.G(class_="labels", elements=[])
            for lbl in edge_labels.get(edge.get("id", ""), []):
                labels_g.elements.append(self._label_to_text(lbl))
            if labels_g.elements:
                edge_group.elements.append(labels_g)

            if edge_group.elements:
                edges_root.elements.append(edge_group)

        if not edges_root.elements:
            return None

        return edges_root

    # ------------------------------------------------------------------ #
    # Edge styling
    # ------------------------------------------------------------------ #
    def _edge_rendering(self, edge: Dict) -> Dict[str, Optional[str]]:
        """
        Map ELK's org.eclipse.elk.edge.type option to SVG styling. Defaults to
        the previous behavior (filled arrow at the target).
        """
        edge_type = (
            self._option_value(
                edge,
                "org.eclipse.elk.edge.type",
                "elk.edge.type",
            )
            or edge.get("type")
        )
        edge_type = str(edge_type).upper() if edge_type else ""

        # Defaults preserve backward compatibility.
        render = {
            "marker_start": None,
            "marker_end": "url(#arrow)",
            "stroke_dasharray": None,
        }

        if edge_type in ("NONE", "UNDIRECTED"):
            render.update({"marker_end": None})
        elif edge_type == "DIRECTED":
            render.update({"marker_end": "url(#arrow)"})
        elif edge_type == "ASSOCIATION":
            render.update({"marker_end": "url(#arrow-open)"})
        elif edge_type == "DEPENDENCY":
            render.update(
                {"marker_end": "url(#arrow-open)", "stroke_dasharray": "6 3"}
            )
        elif edge_type == "GENERALIZATION":
            render.update({"marker_end": "url(#triangle-hollow)"})

        return render

    # ------------------------------------------------------------------ #
    # Geometry helpers
    # ------------------------------------------------------------------ #
    def _canvas_size(self) -> Tuple[Number, Number]:
        width = self.graph.get("width")
        height = self.graph.get("height")
        if width is None or height is None:
            max_x = max((n["x"] + n.get("width", 0) for n in self.nodes), default=0)
            max_y = max((n["y"] + n.get("height", 0) for n in self.nodes), default=0)
            width = max_x
            height = max_y

        return width + self.padding * 2, height + self.padding * 2

    def _port_center(self, port_id: str) -> Optional[Point]:
        port = self.port_lookup.get(port_id)
        if not port:
            return None
        return (
            port["x"] + port.get("width", 0) / 2,
            port["y"] + port.get("height", 0) / 2,
        )

    def _apply_offset(self, point: Dict, offset: Point) -> Point:
        return point.get("x", 0) + offset[0], point.get("y", 0) + offset[1]

    def _section_points(
        self, edge: Dict, section: Dict, offset: Point
    ) -> List[Point]:
        pts: List[Point] = []

        start = section.get("startPoint")
        if start:
            pts.append(self._apply_offset(start, offset))
        else:
            start_port = (edge.get("sources") or [None])[0]
            start_pos = self._port_center(start_port) if start_port else None
            if start_pos:
                pts.append(start_pos)

        for bend in section.get("bendPoints", []) or []:
            pts.append(self._apply_offset(bend, offset))

        end = section.get("endPoint")
        if end:
            pts.append(self._apply_offset(end, offset))
        else:
            target_port = (edge.get("targets") or [None])[0]
            end_pos = self._port_center(target_port) if target_port else None
            if end_pos:
                pts.append(end_pos)

        return pts

    def _fallback_section(self, edge: Dict, offset: Point) -> Optional[Dict]:
        """Create a section when ELK did not emit one."""
        start_port = (edge.get("sources") or [None])[0]
        end_port = (edge.get("targets") or [None])[0]
        start_center = self._port_center(start_port) if start_port else None
        end_center = self._port_center(end_port) if end_port else None
        if not (start_center and end_center):
            return None
        return {
            "startPoint": {"x": start_center[0] - offset[0], "y": start_center[1] - offset[1]},
            "endPoint": {"x": end_center[0] - offset[0], "y": end_center[1] - offset[1]},
            "bendPoints": [],
        }


__all__ = ["ElkGraphSvg"]
