from typing import Callable, List
import ast 
import copy

from graph import OurGraph 



def rename_all_vars(ast_tree: ast.AST, rename_fun: Callable = lambda x: x):
    new_ast_tree = copy.deepcopy(ast_tree)

    for node in ast.walk(new_ast_tree):
        if isinstance(node, ast.Name):
            node.id = rename_fun(node.id)
    return new_ast_tree


def get_assign_node(args: List[ast.arg], vars: List[ast.AST]):
    new_vars_for_args = [ast.Name(id=x.arg, ctx=ast.Store()) for x in args]
    targets_tuple = ast.Tuple(elts=new_vars_for_args,) # ctx=ast.Store()
    value_tuple = ast.Tuple(elts=vars,) # ctx=ast.Load()
    assign_node = ast.Assign(targets=[targets_tuple], value=value_tuple)
    return assign_node    


def expand_function(G: OurGraph, node_id: int):
    def renaming_fun(x):
        return x + "_new"

    G = copy.deepcopy(G)
    node = G.ast_nodes[node_id]
    assert isinstance(node, ast.Call), f"Node {node} is not a function call"

    parent_id = G.get_parent(node_id)
    parent = G.ast_nodes[parent_id]
    assert parent.value == node, f"Parent node {parent} is not the function call {node}"

    function_defs = [
        n for n in G.ast_nodes.values() if isinstance(n, ast.FunctionDef) and n.name == node.func.id and n.lineno < node.lineno
    ]

    assert len(function_defs) > 0, f"No function definition found for {node.func.id}"

    if len(function_defs) > 1:
        print(f"Warning: Multiple function definitions for {node.func.id}")

    fun_def_node = rename_all_vars(function_defs[-1], renaming_fun)
    renamed_args = [ast.arg(arg=renaming_fun(x.arg), annotation=x.annotation) for x in fun_def_node.args.args]

    parent.value = copy.copy(fun_def_node.body[0].value)

    new_assign_node = get_assign_node(renamed_args, node.args)

    grandparent = G.ast_nodes[G.get_parent(parent_id)]
    assert hasattr(grandparent, 'body'), f"Grandparent node {grandparent} has no body"

    call_index = grandparent.body.index(parent)
    grandparent.body.insert(call_index, new_assign_node)
    
    return OurGraph(G.ast_tree)
