import ast
import networkx as nx
import importlib
import utils
importlib.reload(utils)
from utils import node_ignore_ids
from networkx.drawing.nx_pydot import graphviz_layout
import xml.etree.ElementTree as ET
import copy

class Node:
    def __init__(self, node_id, ast_node, parent=None):
        self.node_id = node_id
        self.ast_node = ast_node
        # self.attrs = attrs
        self.parent = parent

    @property
    def attrs(self):
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
    def attrs(self):
        attrs = []
        for k, v in self.parent.ast_node.__dict__.items():
            if isinstance(v, list):
                if self.child.ast_node in v:
                    attrs = [k, v.find(self.child.ast_node)]
            elif self.child.ast_node == v:
                attrs = [k]
        return attrs
    
    # def __str__(self):
    #     return f"{self.ast_node.__class__.__name__}

class OurGraph:
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        self.our_nodes = {}
        self.our_edges = {}
        # self.G = ast_to_networkx(ast_tree)
        self.ast_nodes = {}
        self.G    = nx.DiGraph()
        self.traverse(ast_tree)
        self.edges = self.G.edges
        self.pos = graphviz_layout(self.G, prog="dot")

        x_max = max([x for x, _ in self.pos.values()])
        y_max = max([y for _, y in self.pos.values()])
        self.pos_inv = {k: (x_max-x, y_max-y) for k, (x, y) in self.pos.items()}

    def ast_node(self, node_id) -> ast.AST:
        return self.ast_nodes[node_id]

    def node_attr(self, node_id):
        attrs = node_ignore_ids(self.G, self.G.nodes[node_id])
        attrs.pop("size", None)
        return attrs
    
    def get_parent(self, node_id):
        for parent, child in self.edges:
            if child == node_id:
                return parent
        return None
    
    
    def traverse(self, node, parent=None):
        self.ast_nodes[id(node)] = node
        our_node = Node(id(node), node, parent=parent)
        if parent is not None:
            # our_parent = self.our_nodes[id(parent)]
            self.G.add_edge(parent, id(node))

        attrs = {}
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                attrs[field] = [id(item) for item in value if isinstance(item, ast.AST)]
                for item in value:
                    if isinstance(item, ast.AST):
                        self.traverse(item, id(node))
            elif isinstance(value, ast.AST):
                attrs[field] = id(value)
                self.traverse(value, id(node))
            else:
                attrs[field] = value
            if 'name' in attrs:
                attrs['fun_name'] = attrs.pop('name')

        self.G.nodes[id(node)].update(attrs)
        self.our_nodes[id(node)] = our_node



    def from_file(filename):
        with open(filename, 'r') as file:
            code = file.read()

        tree = ast.parse(code)
        return OurGraph(tree)