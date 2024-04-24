import ast
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from graph import ASTEdge, Edge, Node, OurGraph, OurGraphWithNewNodes, ASTNode, SyntaxToken, Occurence
from typing import Union, Tuple
from abc import ABC, abstractmethod
PURPLE  = "#CCCCFF"
MID_PURPLE = "#CC99FF"
BLUE    = "#CCE5FF"
MID_BLUE = "#66B2FF"
YELLOW  = "#FFF2CC"
ORANGE  = "#FFD9B3"
RED     = "#FFCCCC"
GREEN   = "#D6FFC9"
WHITE   = "#FFFFFF"
BLACK   = "#000000"
PINK    = "#FFCCFF"
CYAN    = "#CCFFFF"
GREY    = "#E6E6E6"
WHITE   = "#FFFFFF"


AST_NODE_COLORS = {
    'Module': MID_PURPLE,

    'Interactive': ORANGE,
    'Expression':  ORANGE,
    'Suite':       ORANGE,

    'FunctionDef': MID_BLUE,
    'AsyncFunctionDef': MID_BLUE,
    'ClassDef': MID_BLUE,

    'Name': BLUE,

    'Return': GREEN,
    'Delete': GREEN,
    'Assign': GREEN,
    'AugAssign': GREEN,
    'AnnAssign': GREEN,

    'For': CYAN,
    'AsyncFor': CYAN,
    'While': CYAN,
    'If': CYAN,
    'With': CYAN,
    'AsyncWith': CYAN,

    'Raise': RED,
    'Try': RED,
    'Assert': RED,
    'Import': RED,
    'ImportFrom': RED,
    'Global': RED,
    'Nonlocal': RED,
    'Expr': RED,
    'Pass': RED,
    'Break': RED,
    'Continue': RED,

    'BoolOp': PURPLE,
    'BinOp':  PURPLE,
    'UnaryOp':PURPLE,
    'Lambda': PURPLE,
    'IfExp':  PURPLE,

    'Dict': ORANGE,
    'Set': ORANGE,
    'ListComp': ORANGE,
    'SetComp': ORANGE,
    'DictComp': ORANGE,
    'GeneratorExp': ORANGE,
    'List': ORANGE,
    'Tuple': ORANGE,

    'Await': PINK,
    'Yield': PINK,
    'YieldFrom': PINK,
    'Compare': PINK,
    'Call': PINK,

    'Num': YELLOW,
    'Str': YELLOW,
    'FormattedValue': YELLOW,
    'JoinedStr': YELLOW,
    'Bytes': YELLOW,
    'NameConstant': YELLOW,
    'Ellipsis': YELLOW,
    'Constant': YELLOW,
    'Attribute': YELLOW,
    'Subscript': YELLOW,
    'Starred': YELLOW,

    'Store': WHITE,
    'Load': WHITE,

}

NEWLINE = '&lt;br&gt;'

class NodeStyle(ABC):
    def __init__(self, node):
        self.node = node

    @abstractmethod
    def node_html_label(self):
        pass

    @abstractmethod
    def color(self):
        pass

    @abstractmethod
    def style(self):
        pass

    def to_xml(self, pos: Tuple[float, float]):
        x, y = pos
        x = x * 1.3
        y = y * 1.3
        width = 120
        height = 60
        point_xml = ET.Element('mxGeometry')
        point_xml.set('x', str(x))
        point_xml.set('y', str(y))
        point_xml.set('width', str(width))
        point_xml.set('height', str(height))
        point_xml.set('as', "geometry")
        
        box = ET.Element('mxCell')
        box.set('id', str(self.node.id))
        box.set('value', self.node_html_label())
        box.set('style', self.style())
        box.set('parent', "1")
        box.set('vertex', "1")
        box.append(point_xml)

        return box


class ASTNodeStyle(NodeStyle):
    def __init__(self, node: ASTNode):
        self.node = node

    def color(self):
        return AST_NODE_COLORS.get(self.node.ast_node.__class__.__name__, GREY)
    
    def style(self):
        return f'rounded=1;whiteSpace=wrap;html=1;fillColor={self.color()};strokeColor=#000000;'

    def node_html_label(self):
        attrs = {k: v for k, v in self.node.attrs.items() if k not in ('lineno', 'col_offset', 'end_lineno', 'end_col_offset')}
        label = '<br>'.join([
            "<b>" + self.node.ast_node.__class__.__name__ + "</b>"
        ]
        +
        [f"{key}: {value}" for key, value in attrs.items() if key != 'type']
        )
        return label
    
    # def to_xml(self, pos: Tuple[float]) -> str:
    #     if isinstance(self.node.ast_node, ast.Load) or isinstance(self.node.ast_node, ast.Store): 
    #         return ""
        
    #     return super().to_xml(pos)
    
class SyntaxTokenStyle(NodeStyle):
    def __init__(self, node: SyntaxToken):
        self.node = node

    def color(self):
        return YELLOW
    
    def style(self):
        return f'rounded=1;whiteSpace=wrap;html=1;fillColor={self.color()};strokeColor=#000000;'
    
    def node_html_label(self):
        attrs = {k: v for k, v in self.node.attrs.items() if k not in ('lineno', 'col_offset', 'end_lineno', 'end_col_offset')}
        label = '<br>'.join([
            "<b>" + self.node.__class__.__name__ + "</b>"
        ]
        +
        [f"{key}: {value}" for key, value in attrs.items()]
        )
        return label

class EdgeStyle(ABC):
    def __init__(self, edge: Edge):
        self.edge = edge

    @abstractmethod
    def color(self):
        pass

    @property
    @abstractmethod
    def style(self):
        # "endArrow=classic;html=1;"
        pass

    @property
    @abstractmethod
    def value(self):
        pass

    def to_xml(self):
        source_id, target_id = self.edge.id

        edge_id = f'{source_id}_{target_id}'
        # value = 
        mxCell = ET.Element('mxCell', id=edge_id, value=self.value, style=self.style, parent="1", source=str(source_id), target=str(target_id), edge="1")

        # Create mxGeometry element
        mxGeometry = ET.SubElement(mxCell, 'mxGeometry', width="50", height="50", relative="1")
        mxGeometry.set('as', 'geometry')
        # Create mxPoint1 using ET.Element and set its attributes
        mxPoint1 = ET.Element('mxPoint')
        mxPoint1.set('x', '400')
        mxPoint1.set('y', '440')
        mxPoint1.set('as', 'sourcePoint')

        # Create mxPoint2 using ET.Element and set its attributes
        mxPoint2 = ET.Element('mxPoint')
        mxPoint2.set('x', '450')
        mxPoint2.set('y', '390')
        mxPoint2.set('as', 'targetPoint')

        # Append mxPoint1 and mxPoint2 to mxGeometry
        mxGeometry.append(mxPoint1)
        mxGeometry.append(mxPoint2)

        return mxCell
    
class ASTEdgeStyle(EdgeStyle):
    def __init__(self, edge: ASTEdge):
        self.edge = edge

    @property
    def color(self):
        return '#000000'
    
    @property
    def style(self):
        return f'endArrow=classic;html=1;strokeColor={self.color};'
    
    @property
    def value(self):
        return str(self.edge.attrs)
    
    # def to_xml(self):
    #     return super().to_xml()

class OccurenceStyle(EdgeStyle):
    def __init__(self, edge: Occurence):
        self.edge = edge

    @property
    def color(self):
        return '#000000'
    
    @property
    def opacity(self):
        return 10
    
    @property
    def style(self):
        style = "edgeStyle=segmentEdgeStyle;endArrow=classic;html=1;rounded=1;endSize=8;startSize=8;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;opacity=20;shadow=0;dashed=1;jumpSize=6;strokeColor=#3333FF;"
        # style = "edgeStyle=segmentEdgeStyle;endArrow=classic;html=1;rounded=1;endSize=8;startSize=8;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;opacity=20;shadow=0;" 
        # style = "edgeStyle=segmentEdgeStyle;endArrow=classic;html=1;curved=0;rounded=0;endSize=8;startSize=8;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" 
        return style
        # return f'endArrow=classic;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;'
    
    @property
    def value(self):
        return ""

def get_style_cls(element: Union[Node, Edge]):
    if element.__class__.__name__ == 'SyntaxToken':
        return SyntaxTokenStyle 
    elif element.__class__.__name__ == 'Occurence':
        return OccurenceStyle
    elif element.__class__.__name__ == 'ASTEdge':
        return ASTEdgeStyle
    elif element.__class__.__name__ == 'ASTNode':
        return ASTNodeStyle
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
    x_scaling: int = 1
    y_scaling: int = 1
    box_width: int = 120
    box_height: int = 60
    
    def graph_to_xml(self, G: Union[OurGraph, OurGraphWithNewNodes]):
        # print('here', isinstance(G, OurGraphWithNewNodes), type(G) is OurGraphWithNewNodes)
        
        mxfile = ET.Element('mxfile', host="65bd71144e")

        # Create diagram element
        diagram = ET.SubElement(mxfile, 'diagram', id="RFndyrCF2-3MIdXtw8gX", name="Page-1")

        # Create mxGraphModel element
        mxGraphModel = ET.SubElement(diagram, 'mxGraphModel', dx="422", dy="816", grid="1", gridSize="10",
                                    guides="1", tooltips="1", connect="1", arrows="1", fold="1",
                                    page="1", pageScale="1", pageWidth="850", pageHeight="1100",
                                    math="0", shadow="0")

        # Create root element
        root = ET.SubElement(mxGraphModel, 'root')

        # Create mxCell elements
        ET.SubElement(root, 'mxCell', id="0")
        ET.SubElement(root, 'mxCell', id="1", parent="0")

        for node in G.our_nodes.values():
            style = get_style_cls(node)
            root.append(style(node).to_xml(G.pos_inv[node.id]))

        for edge in G.our_edges.values():
            style = get_style_cls(edge)
            root.append(style(edge).to_xml())

        # if isinstance(G, OurGraphWithNewNodes):
        for node in G.syntax_tokens.values():
            style = get_style_cls(node)
            root.append(style(node).to_xml(G.pos_inv[node.id]))
        for edge in G.occurences.values():
            style = get_style_cls(edge)
            root.append(style(edge).to_xml())

        return (mxfile)