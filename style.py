from dataclasses import dataclass
import xml.etree.ElementTree as ET

PURPLE  = "#CCCCFF"
BLUE    = "#CCE5FF"
YELLOW  = "#FFF2CC"
ORANGE  = "#FFD9B3"
RED     = "#FFCCCC"
GREEN   = "#CCFFCC"
WHITE   = "#FFFFFF"
BLACK   = "#000000"


AST_NODE_COLORS = {
    'Module': PURPLE,
    'Interactive': BLUE,
    'Expression': YELLOW,
    'Suite': ORANGE,
    'FunctionDef': RED,
    'AsyncFunctionDef': GREEN,
    'ClassDef': PURPLE,
    'Return': BLUE,
    'Delete': YELLOW,
    'Assign': ORANGE,
    'AugAssign': RED,
    'AnnAssign': GREEN,
    'For': PURPLE,
    'AsyncFor': BLUE,
    'While': YELLOW,
    'If': ORANGE,
    'With': RED,
    'AsyncWith': GREEN,
    'Raise': PURPLE,
    'Try': BLUE,
    'Assert': YELLOW,
    'Import': ORANGE,
    'ImportFrom': RED,
    'Global': GREEN,
    'Nonlocal': PURPLE,
    'Expr': BLUE,
    'Pass': YELLOW,
    'Break': ORANGE,
    'Continue': RED,
    'BoolOp': GREEN,
    'BinOp': PURPLE,
    'UnaryOp': BLUE,
    'Lambda': YELLOW,
    'IfExp': ORANGE,
    'Dict': RED,
    'Set': GREEN,
    'ListComp': PURPLE,
    'SetComp': BLUE,
    'DictComp': YELLOW,
    'GeneratorExp': ORANGE,
    'Await': RED,
    'Yield': GREEN,
    'YieldFrom': PURPLE,
    'Compare': BLUE,
    'Call': YELLOW,
    'Num': ORANGE,
    'Str': RED,
    'FormattedValue': GREEN,
    'JoinedStr': PURPLE,
    'Bytes': BLUE,
    'NameConstant': YELLOW,
    'Ellipsis': ORANGE,
    'Constant': RED,
    'Attribute': GREEN,
    'Subscript': PURPLE,
    'Starred': BLUE,
    'Name': YELLOW,
    'List': ORANGE,
    'Tuple': RED
}

NEWLINE = '&lt;br&gt;'


@dataclass
class OurGraphToXML:
    x_scaling: int = 1
    y_scaling: int = 1
    box_width: int = 120
    box_height: int = 60

    def node_html_label(self, G, node_id):
        attrs = G.node_attr(node_id)
        label = '<br>'.join([
            "<b> type: " + G.ast_nodes[node_id].__class__.__name__ + "</b>"
        ]
        +
        [f"{key}: {value}" for key, value in attrs.items() if key != 'type']
        )
     

        return label
    
    def node_to_xml(self, G, node_id):
        pos = G.pos_inv[node_id]
        x, y = pos
        x = x * self.x_scaling
        y = y * self.y_scaling
        width = self.box_width
        height = self.box_height
        point_xml = ET.Element('mxGeometry')
        point_xml.set('x', str(x))
        point_xml.set('y', str(y))
        point_xml.set('width', str(width))
        point_xml.set('height', str(height))
        point_xml.set('as', "geometry")
        
        box = ET.Element('mxCell')
        box.set('id', str(node_id))
        label = self.node_html_label(G, node_id)
        box.set('value', label)
        color = AST_NODE_COLORS.get(G.ast_nodes[node_id].__class__.__name__, YELLOW)

        box.set('style', f'rounded=1;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#000000;')
        box.set('parent', "1")
        box.set('vertex', "1")
        box.append(point_xml)

        return box

    def edge_to_xml(self, source_id, target_id):
        edge_id = f'{source_id}_{target_id}'
        mxCell = ET.Element('mxCell', id=edge_id, value="", style="endArrow=classic;html=1;", parent="1", source=str(source_id), target=str(target_id), edge="1")

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
    
    def graph_to_xml(self, G):
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

        for node in G.G.nodes:
            root.append(self.node_to_xml(G, node))

        for (source_id, target_id) in G.edges():
            root.append(self.edge_to_xml(source_id, target_id))

        return (mxfile)