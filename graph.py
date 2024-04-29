import ast
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
from typing import Dict, List, Tuple
import astor
import copy
from abc import ABC, abstractmethod


class Node(ABC):
    def __init__(self, ast_node: ast.AST, parent=None):
        self.ast_node = ast_node
        self.parent = parent

    @property
    @abstractmethod
    def id(self) -> int:
        pass

    @property
    @abstractmethod
    def attrs(self) -> Dict:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


class Edge(ABC):
    def __init__(self, parent: Node, child: Node):
        self.parent = parent
        self.child = child

    @property
    def id(self) -> Tuple[int, int]:
        return (self.parent.id, self.child.id)

    @property
    @abstractmethod
    def attrs(self) -> List:
        pass


class ASTNode(Node):
    def __init__(self, node_id: int, ast_node: ast.AST, parent=None):
        self.node_id = node_id
        self.ast_node = ast_node
        self.parent = parent

    @property
    def id(self) -> int:
        return self.node_id

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.node_id}, {repr_ast(self.ast_node)})"
        )

    @property
    def attrs(self) -> Dict:
        d = self.ast_node.__dict__

        def ignore(v):
            return isinstance(v, list) or v is None or isinstance(v, ast.AST)

        d = {k: v for k, v in d.items() if not ignore(v)}
        d.pop("parent", None)

        if hasattr(self.ast_node, "ctx"):
            d["ctx"] = self.ast_node.ctx.__class__.__name__
        return d


class ASTEdge(Edge):
    def __init__(self, parent: ASTNode, child: ASTNode):
        self.parent = parent
        self.child = child

    @property
    def id(self) -> Tuple[int, int]:
        return (self.parent.id, self.child.id)

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


class SyntaxToken(Node):
    def __init__(
        self, name: str, scope: ast.FunctionDef, occurences: List[ASTNode] = []
    ):
        self.name = name
        self.scope = scope
        self.occurences = occurences

    @property
    def id(self):
        return f"stx_{self.name}_{id(self.scope)}"

    @property
    def attrs(self):
        return {"name": self.name, "scope": self.scope.name}

    def __repr__(self):
        return f"SyntaxToken({self.name}, scope={self.scope.name})"


class Occurence(Edge):
    def __init__(self, node: ASTNode, token: SyntaxToken):
        self.parent = token
        self.child = node

    def __repr__(self):
        return str(self.__dict__)

    @property
    def attrs(self):
        return {}


class TravesalInfo:
    def __init__(self, currect_scope: int, lookup: Dict[int, Dict[str, SyntaxToken]]):
        self.lookup = lookup
        self.current_scope = currect_scope


def repr_ast(node: ast.AST):
    d = {}
    for field, value in ast.iter_fields(node):
        if isinstance(value, list):
            d[field] = "[...]"
        elif isinstance(value, ast.AST):
            d[field] = str(value.__class__.__name__)
        else:
            d[field] = value
    s = ", ".join([f"{k}={v}" for k, v in d.items()])
    # s = f"{node.__class__.__name__}({s})"
    return s


class CodeGraph:
    def __init__(self, ast_tree: ast.AST):
        self._counter = 0
        self._ast_tree: ast.AST = ast_tree
        self.our_nodes: Dict[int, ASTNode] = {}
        self.our_edges: Dict[Tuple, ASTEdge] = {}
        self.syntax_tokens: Dict[str, SyntaxToken] = {}
        self.occurences: Dict[Tuple, Occurence] = {}
        self.ast_nodes: Dict[int, ast.AST] = {}
        self.refresh()

    @property
    def ast_tree(self):
        return self._ast_tree

    def to_source(self):
        return astor.to_source(copy.deepcopy(self._ast_tree))
    
    def copy(self):
        G = copy.deepcopy(self)
        G.refresh()
        return G

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

        self.our_nodes: Dict[int, ASTNode] = {}
        self.our_edges: Dict[Tuple, ASTEdge] = {}
        self.ast_nodes: Dict[int, ast.AST] = {}
        self._nxG = nx.DiGraph()
        self.traverse(self._ast_tree)
        self.edges = self._nxG.edges
        self.pos = graphviz_layout(self._nxG, prog="dot")
        y_max = max([y for _, y in self.pos.values()])
        self.pos_inv = {k: (x, y_max - y) for k, (x, y) in self.pos.items()}

        info = self.traverse_syntax_tokens(
            self.ast_tree.body[0], TravesalInfo(self.ast_tree.body[0], {})
        )
        self.lookup = info.lookup
        self.syntax_tokens = {w.id: w for v in self.lookup.values() for w in v.values()}

        # token_pos = {token.id: (-150, 50*i) for i, token in enumerate(sorted(self.syntax_tokens.values(), key=lambda x: x.scope.lineno))}
        token_pos = {
            token.id: (-150, 50 * i)
            for i, token in enumerate(self.syntax_tokens.values())
        }
        self.pos_inv = {**self.pos_inv, **token_pos}
        occurences = [
            Occurence(node, token)
            for token in self.syntax_tokens.values()
            for node in token.occurences
        ]
        self.occurences = {o.id: o for o in occurences}

    def traverse(self, node: ast.AST, parent: ASTNode = None):
        node_id = id(node)
        self.ast_nodes[node_id] = node
        our_node = ASTNode(node_id, node, parent=parent)

        if not (isinstance(node, ast.Store) or isinstance(node, ast.Load)):
            self.our_nodes[node_id] = our_node

        if parent is not None:
            self._nxG.add_edge(parent.node_id, node_id)

            if not (isinstance(node, ast.Store) or isinstance(node, ast.Load)):
                self.our_edges[(parent.node_id, node_id)] = ASTEdge(parent, our_node)

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
        if (
            "name" in attrs
        ):  # networkx uses name for node_id, ast uses name for function name
            attrs["fun_name"] = attrs.pop("name")
        self._nxG.nodes[node_id].update(attrs)

    @classmethod
    def from_file(cls, filename):
        with open(filename, "r") as file:
            code = file.read()

        tree = ast.parse(code)
        return cls(tree)

    def traverse_syntax_tokens(self, node: ast.AST, info: TravesalInfo):
        name = (
            node.arg
            if isinstance(node, ast.arg)
            else node.id
            if isinstance(node, ast.Name)
            else None
        )
        if name is not None:
            if name not in info.lookup[id(info.current_scope)]:
                token = SyntaxToken(name, info.current_scope, occurences=[])
                info.lookup[id(info.current_scope)][name] = token

            info.lookup[id(info.current_scope)][name].occurences.append(
                self.our_nodes[id(node)]
            )

        if isinstance(node, ast.FunctionDef):
            lookup = info.lookup
            lookup[id(node)] = {}
            info = TravesalInfo(node, info.lookup)

        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.traverse_syntax_tokens(item, info)
            elif isinstance(value, ast.AST):
                self.traverse_syntax_tokens(value, info)
            else:
                pass

        return info


class OurGraphWithNewNodes(CodeGraph):
    pass
