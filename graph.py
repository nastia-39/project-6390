import ast
import networkx as nx
import importlib
import utils
importlib.reload(utils)
from networkx.drawing.nx_pydot import graphviz_layout
from typing import Dict, List, Tuple
from functools import cached_property
import uuid 
import astor

class Node:
    def __init__(self, node_id: int, ast_node: ast.AST, parent=None):
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
    def __init__(self, parent: Node, child: Node):
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
        self._counter = 0
        self._ast_tree: ast.AST = ast_tree
        self.our_nodes: Dict[int, Node] = {}
        self.our_edges: Dict[Tuple, Edge] = {}

        self.ast_nodes: Dict[int, ast.AST] = {} 
        self._nxG: nx.DiGraph = nx.DiGraph()
        self.traverse(ast_tree)
        self.edges = self._nxG.edges
        self.pos = graphviz_layout(self._nxG, prog="dot")
        y_max = max([y for _, y in self.pos.values()])
        self.pos_inv = {k: (x, y_max - y) for k, (x, y) in self.pos.items()}

    @property
    def ast_tree(self):
        return self._ast_tree
    
    def to_source(self):
        return astor.to_source(self._ast_tree)

    @property
    def load_node(self) -> ast.Load:
        for node in self.ast_nodes.values():
            if isinstance(node, ast.Load):
                return node
        return ast.Load()
    
    @property
    def store_node(self) -> ast.Store:
        for node in self.ast_nodes.values():
            if isinstance(node, ast.Store):
                return node
        return ast.Store()

    def ast_node(self, node_id) -> ast.AST:
        return self.ast_nodes[node_id]
    
    def get_parent(self, node_id):
        for parent, child in self.edges:
            if child == node_id:
                return parent
        return None
    
    def refresh(self):
        """
        should be called after modifying the ast_tree 
        """
        self._counter = 0
        self.our_nodes: Dict[int, Node] = {}
        self.our_edges: Dict[Tuple, Edge] = {}

        self.ast_nodes: Dict[int, ast.AST] = {} 
        self._nxG = nx.DiGraph()
        self.traverse(self._ast_tree)
        self.edges = self._nxG.edges
        self.edges = self._nxG.edges
        self.pos = graphviz_layout(self._nxG, prog="dot")
        y_max = max([y for _, y in self.pos.values()])
        self.pos_inv = {k: (x, y_max - y) for k, (x, y) in self.pos.items()}
    
    def traverse(self, node: ast.AST, parent: Node = None):
        # node_id = f"v_{self._counter}"
        node_id = id(node)
        self._counter += 1
        self.ast_nodes[node_id] = node
        our_node = Node(node_id, node, parent=parent)
        self.our_nodes[node_id] = our_node

        if parent is not None:
            self._nxG.add_edge(parent.node_id, node_id)
            self.our_edges[(parent.node_id, node_id)] = Edge(parent, our_node)
            
        self.our_nodes[node_id] = our_node
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.traverse(item, our_node)
            elif isinstance(value, ast.AST):
                self.traverse(value, our_node)
            else:
                pass
        
        # stores node attrs in networkx graph
        attrs = our_node.attrs
        if 'name' in attrs:  #networkx uses name for node_id, ast uses name for function name
            attrs['fun_name'] = attrs.pop('name')
        self._nxG.nodes[node_id].update(attrs)


    def from_file(filename):
        with open(filename, 'r') as file:
            code = file.read()

        tree = ast.parse(code)
        return OurGraph(tree)