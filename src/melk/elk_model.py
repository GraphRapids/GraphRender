from enum import Enum
from uuid import uuid4
from typing import Any, Dict, List, Union
from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator

def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"

class Properties(BaseModel):
    model_config = {"extra": "allow"}

class Direction(str, Enum):
    UNDEFINED = "UNDEFINED"
    RIGHT = "RIGHT"
    LEFT = "LEFT"
    DOWN = "DOWN"
    UP = "UP"

class NodeLabelPlacement(str, Enum):
    INSIDE = "INSIDE"
    OUTSIDE = "OUTSIDE"
    H_LEFT = "H_LEFT"
    H_CENTER = "H_CENTER"
    H_RIGHT = "H_RIGHT"
    V_TOP = "V_TOP"
    V_CENTER = "V_CENTER"
    V_BOTTOM = "V_BOTTOM"
    H_PRIORITY = "H_PRIORITY"

class PortLabelPlacement(str, Enum):
    INSIDE = "INSIDE"
    OUTSIDE = "OUTSIDE"
    NEXT_TO_PORT_IF_POSSIBLE = "NEXT_TO_PORT_IF_POSSIBLE"
    ALWAYS_SAME_SIDE = "ALWAYS_SAME_SIDE"
    ALWAYS_OTHER_SAME_SIDE = "ALWAYS_OTHER_SAME_SIDE"
    SPACE_EFFICIENT = "SPACE_EFFICIENT"

class PortSide(str, Enum):
    UNDEFINED = "UNDEFINED"
    NORTH = "NORTH"
    EAST = "EAST"
    SOUTH = "SOUTH"
    WEST = "WEST"

class EdgeType(str, Enum):
    NONE = "NONE"
    DIRECTED = "DIRECTED"
    UNDIRECTED = "UNDIRECTED"
    ASSOCIATION = "ASSOCIATION"
    GENERALIZATION = "GENERALIZATION"
    DEPENDENCY = "DEPENDENCY"

class LayeringStrategy(str, Enum):
    NETWORK_SIMPLEX = "NETWORK_SIMPLEX"
    LONGEST_PATH = "LONGEST_PATH"
    LONGEST_PATH_SOURCE = "LONGEST_PATH_SOURCE"
    COFFMAN_GRAHAM = "COFFMAN_GRAHAM"
    INTERACTIVE = "INTERACTIVE"
    STRETCH_WIDTH = "STRETCH_WIDTH"
    MIN_WIDTH = "MIN_WIDTH"
    BF_MODEL_ORDER = "BF_MODEL_ORDER"
    DF_MODEL_ORDER = "DF_MODEL_ORDER"

class NodeSizeConstraint(str, Enum):
    PORTS = "PORTS"
    PORT_LABELS = "PORT_LABELS"
    NODE_LABELS = "NODE_LABELS"
    MINIMUM_SIZE = "MINIMUM_SIZE"

class NodeSizeOption(str, Enum):
    DEFAULT_MINIMUM_SIZE = "DEFAULT_MINIMUM_SIZE"
    MINIMUM_SIZE_ACCOUNTS_FOR_PADDING = "MINIMUM_SIZE_ACCOUNTS_FOR_PADDING"
    COMPUTE_PADDING = "COMPUTE_PADDING"
    OUTSIDE_NODE_LABELS_OVERHANG = "OUTSIDE_NODE_LABELS_OVERHANG"
    PORTS_OVERHANG = "PORTS_OVERHANG"
    UNIFORM_PORT_SPACING = "UNIFORM_PORT_SPACING"
    FORCE_TABULAR_NODE_LABELS = "FORCE_TABULAR_NODE_LABELS"
    ASYMMETRICAL = "ASYMMETRICAL"

class PortConstraint(str, Enum):
    UNDEFINED = "UNDEFINED"
    FREE = "FREE"
    FIXED_SIDE = "FIXED_SIDE"
    FIXED_ORDER = "FIXED_ORDER"
    FIXED_RATIO = "FIXED_RATIO"
    FIXED_POS = "FIXED_POS"

NodePlacementInput = Union[str, List[NodeLabelPlacement]]
PortPlacementInput = Union[str, List[PortLabelPlacement]]

class NodeLabel(BaseModel):
    text: str = "Node"
    width: float = 100
    height: float = 16
    properties: Properties = Field(default_factory=lambda: Properties(**{"font.size": 16}))

class PortLabel(BaseModel):
    text: str = "Port"
    width: float = 50
    height: float = 8
    properties: Properties = Field(default_factory=lambda: Properties(**{"font.size": 8}))

class EdgeLabel(BaseModel):
    text: str = "Edge"
    width: float = 100
    height: float = 10
    properties: Properties = Field(
        default_factory=lambda: Properties(
            **{"font.size": 10, "edgeLabels.inline": False}
        )
    )

class Port(BaseModel):
    id: str = Field(default_factory=lambda: _gen_id("port"))
    labels: List[PortLabel] = Field(default_factory=list)
    properties: dict = {}
    width: float = 2.0
    height: float = 2.0

class ChildNode(BaseModel):
    id: str = Field(default_factory=lambda: _gen_id("node"))
    type: str = "router"
    icon: str = "mdi:router"
    width: float = 50
    height: float = 50
    labels: List[NodeLabel] = Field(default_factory=list)
    ports: List[Port] = Field(default_factory=list)
    properties: Properties = Field(
        default_factory=lambda: Properties(
            **{
                "portConstraints": "[FREE, FIXED_ORDER]",
                "nodeLabels.placement": "[OUTSIDE, V_BOTTOM, H_CENTER, H_PRIORITY]",
            }
        )
    )

    @field_validator("ports")
    @classmethod
    def port_ids_unique(cls, v: List[Port]):
        ids = [p.id for p in v]
        if len(ids) != len(set(ids)):
            raise ValueError("port ids must be unique within a node")
        return v

class Edge(BaseModel):
    id: str = Field(default_factory=lambda: _gen_id("edge"))
    sources: List[str] = Field(default_factory=list)
    targets: List[str] = Field(default_factory=list)
    labels: List[EdgeLabel] = Field(default_factory=list)
    properties: Properties = Field(
        default_factory=lambda: Properties(
            **{"edge.type": "UNDIRECTED", "edge.thickness": 1}
        )
    )

class LayoutOptions(BaseModel):
    model_config = {"extra": "allow", "populate_by_name": True}

    # Must be emitted as a string "[H_CENTER,V_BOTTOM,OUTSIDE,H_PRIORITY]""
    org_eclipse_elk_nodeLabels_placement: List[NodeLabelPlacement] = Field(
        default_factory=lambda: [
            NodeLabelPlacement.H_CENTER,
            NodeLabelPlacement.V_BOTTOM,
            NodeLabelPlacement.OUTSIDE,
            NodeLabelPlacement.H_PRIORITY,
        ],
        alias="org.eclipse.elk.nodeLabels.placement",
    )

    @field_serializer("org_eclipse_elk_nodeLabels_placement")
    def serialize_node_labels_placement(self, v: List[NodeLabelPlacement], _info):
        return "[" + ",".join(item.value for item in v) + "]"
    
    @field_validator("org_eclipse_elk_nodeLabels_placement", mode="before")
    @classmethod
    def parse_placement(cls, v: NodePlacementInput):
        if isinstance(v, list):
            return v

        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s = s[1:-1].strip()

            if not s:
                return []

            parts = [p.strip() for p in s.split(",") if p.strip()]
            return [NodeLabelPlacement(p) for p in parts]

        return v

    org_eclipse_elk_portLabels_placement: List[PortLabelPlacement] = Field(
        default_factory=lambda: [PortLabelPlacement.OUTSIDE],
        alias="org.eclipse.elk.portLabels.placement",
    )

    @field_serializer("org_eclipse_elk_portLabels_placement")
    def serialize_port_labels_placement(self, v: List[PortLabelPlacement], _info):
        return "[" + ",".join(item.value for item in v) + "]"

    @field_validator("org_eclipse_elk_portLabels_placement", mode="before")
    @classmethod
    def parse_port_placement(cls, v: Union[str, List[PortLabelPlacement]]):

        if isinstance(v, list):
            return v

        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s = s[1:-1].strip()

            if not s:
                return []

            parts = [p.strip() for p in s.split(",") if p.strip()]
            return [PortLabelPlacement(p) for p in parts]

        return v

    org_eclipse_elk_algorithm: str = Field(
        default="layered", alias="org.eclipse.elk.algorithm"
    )
    org_eclipse_elk_nodeSize_constraints: NodeSizeConstraint = Field(
        default=NodeSizeConstraint.MINIMUM_SIZE, alias="org.eclipse.elk.nodeSize.constraints"
    )
    org_eclipse_elk_nodeSize_options: NodeSizeOption = Field(
        default=NodeSizeOption.DEFAULT_MINIMUM_SIZE, alias="org.eclipse.elk.nodeSize.options"
    )
    org_eclipse_elk_layered_layering_strategy: str = Field(
        default="NETWORK_SIMPLEX", alias="org.eclipse.elk.layered.layering.strategy"
    )
    org_eclipse_elk_aspectRatio: str = Field(
        default="1.414", alias="org.eclipse.elk.aspectRatio"
    )
    org_eclipse_elk_zoomToFit: bool = Field(
        default=True, alias="org.eclipse.elk.zoomToFit"
    )
    org_eclipse_elk_direction: Direction = Field(
        default=Direction.RIGHT, alias="org.eclipse.elk.direction"
    )

    @field_validator("org_eclipse_elk_nodeSize_constraints", mode="before")
    @classmethod
    def parse_node_size_constraints(cls, v: Union[str, NodeSizeConstraint]):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s = s[1:-1].strip()
            if not s:
                return NodeSizeConstraint.MINIMUM_SIZE
            return NodeSizeConstraint(s)
        return v

    @field_validator("org_eclipse_elk_nodeSize_options", mode="before")
    @classmethod
    def parse_node_size_options(cls, v: Union[str, NodeSizeOption]):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s = s[1:-1].strip()
            if not s:
                return NodeSizeOption.DEFAULT_MINIMUM_SIZE
            return NodeSizeOption(s)
        return v

class ElkModel(BaseModel):
    model_config = {"populate_by_name": True}

    id: str = "canvas"
    layoutOptions: LayoutOptions = Field(default_factory=LayoutOptions)
    children: List[ChildNode]
    edges: List[Edge] = Field(default_factory=list)

    @field_validator("children")
    @classmethod
    def children_ids_unique(cls, v: List[ChildNode]):
        ids = [c.id for c in v]
        if len(ids) != len(set(ids)):
            raise ValueError("children id values must be unique")
        return v

    @field_validator("edges")
    @classmethod
    def edge_ids_unique(cls, v: List[Edge]):
        ids = [e.id for e in v]
        if len(ids) != len(set(ids)):
            raise ValueError("edge id values must be unique")
        return v
