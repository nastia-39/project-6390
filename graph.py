import ast
import networkx as nx
import importlib
import utils
importlib.reload(utils)
from utils import node_ignore_ids
from networkx.drawing.nx_pydot import graphviz_layout
import xml.etree.ElementTree as ET


class OurGraph:
    def __init__(self, ast_tree):
        self.ast_tree = ast_tree
        # self.G = ast_to_networkx(ast_tree)
        self.ast_nodes = {}
        self.G    = nx.DiGraph()
        self.traverse(ast_tree)
        self.edges = self.G.edges
        self.pos = graphviz_layout(self.G, prog="dot")

        x_max = max([x for x, _ in self.pos.values()])
        y_max = max([y for _, y in self.pos.values()])
        self.pos_inv = {k: (x_max-x, y_max-y) for k, (x, y) in self.pos.items()}

    def node_attr(self, node_id):
        attrs = node_ignore_ids(self.G, self.G.nodes[node_id])
        attrs.pop("size", None)
        return attrs
    
    
    def traverse(self, node, parent=None):
        self.ast_nodes[id(node)] = node

        if parent is not None:
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


    def from_file(filename):
        with open(filename, 'r') as file:
            code = file.read()

        tree = ast.parse(code)
        return OurGraph(tree)