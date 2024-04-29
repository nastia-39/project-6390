from dataclasses import dataclass
import xml.etree.ElementTree as ET
from graph import (
    ASTEdge,
    Edge,
    Node,
    CodeGraph,
    OurGraphWithNewNodes,
    ASTNode,
    SyntaxToken,
    Occurence,
)
from typing import Union, Tuple
from abc import ABC, abstractmethod
import random

PURPLE = "#CCCCFF"
MID_PURPLE = "#CC99FF"
BLUE = "#CCE5FF"
MID_BLUE = "#66B2FF"
YELLOW = "#FFF2CC"
ORANGE = "#FFD9B3"
RED = "#FFCCCC"
GREEN = "#D6FFC9"
WHITE = "#FFFFFF"
BLACK = "#000000"
PINK = "#FFCCFF"
CYAN = "#CCFFFF"
GREY = "#E6E6E6"
WHITE = "#FFFFFF"


AST_NODE_COLORS = {
    "Module": MID_PURPLE,
    "Interactive": ORANGE,
    "Expression": ORANGE,
    "Suite": ORANGE,
    "FunctionDef": MID_PURPLE,
    "AsyncFunctionDef": MID_PURPLE,
    "ClassDef": MID_PURPLE,
    "Name": BLUE,
    "Return": GREEN,
    "Delete": GREEN,
    "Assign": GREEN,
    "AugAssign": GREEN,
    "AnnAssign": GREEN,
    "For": CYAN,
    "AsyncFor": CYAN,
    "While": CYAN,
    "If": CYAN,
    "With": CYAN,
    "AsyncWith": CYAN,
    "Raise": RED,
    "Try": RED,
    "Assert": RED,
    "Import": RED,
    "ImportFrom": RED,
    "Global": RED,
    "Nonlocal": RED,
    "Expr": RED,
    "Pass": RED,
    "Break": RED,
    "Continue": RED,
    "BoolOp": PURPLE,
    "BinOp": PURPLE,
    "UnaryOp": PURPLE,
    "Lambda": PURPLE,
    "IfExp": PURPLE,
    "Dict": ORANGE,
    "Set": ORANGE,
    "ListComp": ORANGE,
    "SetComp": ORANGE,
    "DictComp": ORANGE,
    "GeneratorExp": ORANGE,
    "List": ORANGE,
    "Tuple": ORANGE,
    "Await": PINK,
    "Yield": PINK,
    "YieldFrom": PINK,
    "Compare": PINK,
    "Call": PINK,
    "Num": YELLOW,
    "Str": YELLOW,
    "FormattedValue": YELLOW,
    "JoinedStr": YELLOW,
    "Bytes": YELLOW,
    "NameConstant": YELLOW,
    "Ellipsis": YELLOW,
    "Constant": YELLOW,
    "Attribute": YELLOW,
    "Subscript": YELLOW,
    "Starred": YELLOW,
    "Store": WHITE,
    "Load": WHITE,
}


@dataclass
class GeneralStyleParams:
    x_scaling: int = 1
    y_scaling: int = 1
    box_width: int = 120
    box_height: int = 60


class NodeXML(ABC):
    def __init__(self, node, params: GeneralStyleParams = GeneralStyleParams()):
        self.node = node
        self.params = params

    @abstractmethod
    def node_html_label(self):
        pass

    @abstractmethod
    def style(self):
        pass

    def to_xml(self, pos: Tuple[float, float]):
        x, y = pos
        x = x * self.params.x_scaling
        y = y * self.params.y_scaling
        width = self.params.box_width
        height = self.params.box_height
        point_xml = ET.Element("mxGeometry")
        point_xml.set("x", str(x))
        point_xml.set("y", str(y))
        point_xml.set("width", str(width))
        point_xml.set("height", str(height))
        point_xml.set("as", "geometry")

        box = ET.Element("mxCell")
        box.set("id", str(self.node.id))
        box.set("value", self.node_html_label())
        box.set("style", self.style().to_html())
        box.set("parent", "1")
        box.set("vertex", "1")
        box.append(point_xml)

        return box


@dataclass
class NodeStyle(ABC):
    def to_html(self):
        return ";".join([f"{key}={value}" for key, value in self.__dict__.items()])


@dataclass
class ASTNodeStyle(NodeStyle):
    # shape: str = "rectangle"
    whiteSpace: str = "wrap"
    html: int = 1
    rounded: int = 1
    fillColor: str = "#CCCCFF"
    strokeColor: str = "#000000"


class ASTNodeXML(NodeXML):
    def __init__(
        self, node: ASTNode, params: GeneralStyleParams = GeneralStyleParams()
    ):
        self.params = params
        self.node = node

    def style(self):
        fillColor = AST_NODE_COLORS.get(self.node.ast_node.__class__.__name__, GREY)
        return ASTNodeStyle(fillColor=fillColor)

    def node_html_label(self):
        attrs = {
            k: v
            for k, v in self.node.attrs.items()
            if k not in ("lineno", "col_offset", "end_lineno", "end_col_offset")
        }
        label = "<br>".join(
            ["<b>" + self.node.ast_node.__class__.__name__ + "</b>"]
            + [f"{key}: {value}" for key, value in attrs.items() if key != "type"]
        )
        return label


class SyntaxTokenStyle(NodeXML):
    def __init__(
        self, node: SyntaxToken, params: GeneralStyleParams = GeneralStyleParams()
    ):
        self.node = node
        self.params = params

    def style(self):
        return ASTNodeStyle(fillColor=MID_BLUE, strokeColor=MID_BLUE)

    def node_html_label(self):
        attrs = {
            k: v
            for k, v in self.node.attrs.items()
            if k not in ("lineno", "col_offset", "end_lineno", "end_col_offset")
        }
        label = "<br>".join(
            ["<b>" + self.node.__class__.__name__ + "</b>"]
            + [f"{key}: {value}" for key, value in attrs.items()]
        )
        return label


@dataclass
class EdgeStyle(ABC):
    def to_html(self):
        return ";".join([f"{key}={value}" for key, value in self.__dict__.items()])


class EdgeXML(ABC):
    def __init__(self, edge: Edge):
        self.edge = edge

    @abstractmethod
    def style(self) -> EdgeStyle:
        pass

    @property
    @abstractmethod
    def value(self):
        pass

    def to_xml(self):
        source_id, target_id = self.edge.id

        edge_id = f"{source_id}_{target_id}"
        # value =
        mxCell = ET.Element(
            "mxCell",
            id=edge_id,
            value=self.value,
            style=self.style.to_html(),
            parent="1",
            source=str(source_id),
            target=str(target_id),
            edge="1",
        )

        # Create mxGeometry element
        mxGeometry = ET.SubElement(
            mxCell, "mxGeometry", width="50", height="50", relative="1"
        )
        mxGeometry.set("as", "geometry")
        # Create mxPoint1 using ET.Element and set its attributes
        mxPoint1 = ET.Element("mxPoint")
        mxPoint1.set("x", "400")
        mxPoint1.set("y", "440")
        mxPoint1.set("as", "sourcePoint")

        # Create mxPoint2 using ET.Element and set its attributes
        mxPoint2 = ET.Element("mxPoint")
        mxPoint2.set("x", "450")
        mxPoint2.set("y", "390")
        mxPoint2.set("as", "targetPoint")

        # Append mxPoint1 and mxPoint2 to mxGeometry
        mxGeometry.append(mxPoint1)
        mxGeometry.append(mxPoint2)

        return mxCell


@dataclass
class ASTEdgeStyle(EdgeStyle):
    endArrow: str = "classic"
    html: int = 1
    strokeColor: str = "#000000"


class ASTEdgeXML(EdgeXML):
    def __init__(self, edge: ASTEdge):
        self.edge = edge

    @property
    def style(self) -> ASTEdgeStyle:
        return ASTEdgeStyle()

    @property
    def value(self):
        return str(self.edge.attrs)


@dataclass
class OccurenceStyle:
    edgeStyle: str = "segmentEdgeStyle"
    endArrow: str = "classic"
    html: int = 1
    rounded: int = 1
    endSize: int = 8
    startSize: int = 8
    # exitX: float = 1
    # exitY: float = 0.5
    # exitDx: int = 0
    # exitDy: int = 0
    entryX: float = 0.25
    entryY: float = 0
    entryDx: int = 0
    entryDy: int = 0
    opacity: int = 70
    shadow: int = 0
    dashed: int = 1
    jumpSize: int = 6
    strokeColor: str = MID_BLUE

    def to_html(self):
        return ";".join([f"{key}={value}" for key, value in self.__dict__.items()])


class OccurenceXML(EdgeXML):
    def __init__(self, edge: Occurence):
        self.edge = edge

    @property
    def style(self) -> str:
        style = OccurenceStyle(entryX=0.25 + random.random() * 0.25)
        return style

    @property
    def value(self):
        return ""


def get_style_cls(element: Union[Node, Edge]):
    if element.__class__.__name__ == "SyntaxToken":
        return SyntaxTokenStyle
    elif element.__class__.__name__ == "Occurence":
        return OccurenceXML
    elif element.__class__.__name__ == "ASTEdge":
        return ASTEdgeXML
    elif element.__class__.__name__ == "ASTNode":
        return ASTNodeXML
    else:
        raise ValueError(f"Unknown node type: {element}")

    # if isinstance(element, ASTNode):
    #     return ASTNodeStyle
    # elif isinstance(element, SyntaxToken):
    #     return SyntaxTokenStyle
    # elif isinstance(element, ASTEdge):
    #     return ASTEdgeStyle
    # elif isinstance(element, Occurence):
    #     return OccurenceStyle
    # else:
    #     raise ValueError(f"Unknown node type: {element}")





@dataclass
class OurGraphToXML:
    def __init__(self, params: GeneralStyleParams = GeneralStyleParams()):
        self.params = params

    def graph_to_xml(self, G: Union[CodeGraph, OurGraphWithNewNodes]):
        mxfile = ET.Element("mxfile", host="65bd71144e")

        # Create diagram element
        diagram = ET.SubElement(
            mxfile, "diagram", id="code-graph", name="Page-1"
        )

        # Create mxGraphModel element
        mxGraphModel = ET.SubElement(
            diagram,
            "mxGraphModel",
            dx="422",
            dy="816",
            grid="1",
            gridSize="10",
            guides="1",
            tooltips="1",
            connect="1",
            arrows="1",
            fold="1",
            page="1",
            pageScale="1",
            pageWidth="850",
            pageHeight="1100",
            math="0",
            shadow="0",
        )

        # Create root element
        root = ET.SubElement(mxGraphModel, "root")

        # Create mxCell elements
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")

        for node in G.our_nodes.values():
            root.append(ASTNodeXML(node, self.params).to_xml(G.pos_inv[node.id]))

        for edge in G.our_edges.values():
            root.append(ASTEdgeXML(edge).to_xml())

        for node in G.syntax_tokens.values():
            root.append(SyntaxTokenStyle(node, self.params).to_xml(G.pos_inv[node.id]))

        for edge in G.occurences.values():
            root.append(OccurenceXML(edge).to_xml())

        return mxfile
