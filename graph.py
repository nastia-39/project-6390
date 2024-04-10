import ast
import networkx as nx
import importlib
import utils
importlib.reload(utils)
from utils import node_ignore_ids
from networkx.drawing.nx_pydot import graphviz_layout
import xml.etree.ElementTree as ET
import copy
from typing import Dict, List, Tuple

class Node:
    def __init__(self, node_id, ast_node, parent=None):
        self.node_id = node_id
        self.ast_node = ast_node
        # self.attrs = attrs
        self.parent = parent

    @property
    def attrs(self) -> Dict:
        d = self.ast_node.__dict__
        def ignore(v):
            return isinstance(v, list) or v is None or isinstance(v, ast.AST)
        d = {k: v for k, v in d.items() if not ignore(v)}
        d.pop('parent', None)
        return d
    
class Edge:
    def __init__(self, parent, child):
        self.parent = parent
        self.child = child
    
    @property
    def attrs(self) -> List:
        attrs = []
        for k, v in self.parent.ast_node.__dict__.items():
            if isinstance(v, list):
                if self.child.ast_node in v:
                    attrs = [k, v.index(self.child.ast_node)]
            elif self.child.ast_node == v:
                attrs = [k]
        return attrs

class OurGraph:
    def __init__(self, ast_tree: ast.AST):
        self.ast_tree: ast.AST = ast_tree
        self.our_nodes: Dict[int, Node] = {}
        self.our_edges: Dict[Tuple, Edge] = {}

        self.ast_nodes = {} 
        self.nxG: nx.DiGraph = nx.DiGraph()
        self.traverse_new(ast_tree)
        self.edges = self.nxG.edges

        # this code generates position of the nodes for plotting
        self.pos = graphviz_layout(self.nxG, prog="dot")
        x_max = max([x for x, _ in self.pos.values()])
        y_max = max([y for _, y in self.pos.values()])
        self.pos_inv = {k: (x_max-x, y_max-y) for k, (x, y) in self.pos.items()}

    def ast_node(self, node_id) -> ast.AST:
        return self.ast_nodes[node_id]

    # def node_attr(self, node_id):
    #     attrs = node_ignore_ids(self.G, self.G.nodes[node_id])
    #     attrs.pop("size", None)
    #     return attrs
    
    def get_parent(self, node_id):
        for parent, child in self.edges:
            if child == node_id:
                return parent
        return None
    
    def traverse_new(self, node: ast.AST, parent: Node = None):
        node_id = id(node)
        self.ast_nodes[node_id] = node
        our_node = Node(node_id, node, parent=parent)
        self.our_nodes[id(node)] = our_node

        if parent is not None:
            self.nxG.add_edge(parent.node_id, node_id)
            self.our_edges[(parent.node_id, node_id)] = Edge(parent, our_node)
            
        self.our_nodes[id(node)] = our_node
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.traverse_new(item, our_node)
            elif isinstance(value, ast.AST):
                self.traverse_new(value, our_node)
            else:
                pass
        
        # stores node attrs in networkx graph
        attrs = our_node.attrs
        if 'name' in attrs:  #networkx uses name for node_id, ast uses name for function name
            attrs['fun_name'] = attrs.pop('name')
        self.nxG.nodes[node_id].update(attrs)

    
    # def traverse(self, node, parent=None):
    #     self.ast_nodes[id(node)] = node
    #     our_node = Node(id(node), node, parent=parent)
    #     if parent is not None:
    #         our_parent = self.our_nodes[id(parent)]
    #         self.nxG.add_edge(parent, id(node))

    #     attrs = {}
    #     for field, value in ast.iter_fields(node):
    #         if isinstance(value, list):
    #             attrs[field] = [id(item) for item in value if isinstance(item, ast.AST)]
    #             for item in value:
    #                 if isinstance(item, ast.AST):
    #                     self.traverse(item, id(node))
    #         elif isinstance(value, ast.AST):
    #             attrs[field] = id(value)
    #             self.traverse(value, id(node))
    #         else:
    #             attrs[field] = value
    #         if 'name' in attrs:
    #             attrs['fun_name'] = attrs.pop('name')

    #     self.nxG.nodes[id(node)].update(attrs)
    #     self.our_nodes[id(node)] = our_node



    def from_file(filename):
        with open(filename, 'r') as file:
            code = file.read()

        tree = ast.parse(code)
        return OurGraph(tree)