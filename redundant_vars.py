import ast
import networkx as nx
from typing import Dict, List, Tuple
from graph import OurGraph

class RedundantVariableRemover(ast.NodeTransformer):
    def __init__(self, redundant_vars):
        self.redundant_vars = redundant_vars

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in self.redundant_vars:
                return None  # This removes the node from the AST
        return node  # Otherwise, do not modify

def find_redundant_variables(G: OurGraph):
    redundant_vars = set()
    for node_id, node in G.ast_nodes.items():
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and not is_variable_used(target.id, G.ast_tree):
                redundant_vars.add(target.id)
    return redundant_vars

def is_variable_used(var_name, ast_tree):
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Name) and node.id == var_name and isinstance(node.ctx, ast.Load):
            return True
    return False

def remove_nodes_from_graph(G: OurGraph, nodes_to_remove):
    for node_id in nodes_to_remove:
        G.nxG.remove_node(node_id)
        G.our_nodes.pop(node_id, None)
        G.ast_nodes.pop(node_id, None)
        edges_to_remove = [(parent, child) for parent, child in G.our_edges if child == node_id]
        for edge in edges_to_remove:
            G.our_edges.pop(edge, None)

def remove_redundant_variables(G: OurGraph):
    transformer = RedundantVariableRemover(find_redundant_variables(G))
    new_ast = transformer.visit(G.ast_tree)
    ast.fix_missing_locations(new_ast)
    nodes_to_remove = [node.node_id for node in G.our_nodes.values() if isinstance(node.ast_node, ast.Assign) and node.ast_node not in ast.walk(new_ast)]
    remove_nodes_from_graph(G, nodes_to_remove)
    G.ast_tree = new_ast
    G.__init__(new_ast)
    return G