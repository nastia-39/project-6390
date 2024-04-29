import ast
from graph import CodeGraph

class RedundantVariableRemover(ast.NodeTransformer):
    def __init__(self, redundant_vars):
        self.redundant_vars = redundant_vars

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in self.redundant_vars:
                return None  # Removes the node from the AST
        return self.generic_visit(node)  # Continue traversing the AST

def find_redundant_variables(G: CodeGraph):
    redundant_vars = set()
    for node_id, node in G.our_nodes.items():
        if isinstance(node.ast_node, ast.Assign) and len(node.ast_node.targets) == 1:
            target = node.ast_node.targets[0]
            if isinstance(target, ast.Name) and not is_variable_used(G, target.id):
                redundant_vars.add(target.id)
    return redundant_vars

def is_variable_used(G: CodeGraph, var_name):
    for node in ast.walk(G.ast_tree):
        if isinstance(node, ast.Name) and node.id == var_name and isinstance(node.ctx, ast.Load):
            return True
    return False

def remove_redundant_variables(G: CodeGraph):
    redundant_vars = find_redundant_variables(G)
    transformer = RedundantVariableRemover(redundant_vars)
    new_ast = transformer.visit(G.ast_tree)
    ast.fix_missing_locations(new_ast)
    G.refresh()  # Refreshes the graph to reflect the changes in the AST
    return G