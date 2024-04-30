from typing import Callable, List
import ast 
import copy
from graph import CodeGraph 



def rename_all_vars(ast_tree: ast.AST, rename_fun: Callable = lambda x: x):
    """
    renames all variables in the ast_tree calling rename_fun on each name
    """
    new_ast_tree = copy.deepcopy(ast_tree)

    for node in ast.walk(new_ast_tree):
        if isinstance(node, ast.Name):
            node.id = rename_fun(node.id)
    return new_ast_tree


def get_assign_node(args: List[ast.arg], vars: List[ast.AST]):
    """
    
    """
    new_vars_for_args = [ast.Name(id=x.arg, ctx=ast.Store()) for x in args]
    targets_tuple = ast.Tuple(elts=new_vars_for_args,) #TODO ctx=ast.Store()
    value_tuple = ast.Tuple(elts=vars,) #TODO ctx=ast.Load()
    assign_node = ast.Assign(targets=[targets_tuple], value=value_tuple)

    # new_vars_for_args = [ast.Name(id=x.arg, ctx=ast.Store()) for x in args]
    new_vars = ast.Tuple(elts=[ast.Name(id=x.arg, ctx=ast.Store()) for x in args],) 
    values = ast.Tuple(elts=vars) 
    assign_node = ast.Assign(targets=[new_vars], value=values)

    return assign_node    


def expand_function(G: CodeGraph, node_id: int):
    """
    Suppose we have function f(x, y) = x + y and call it on z = f(1, 2)
    1. retrieve the tree that corresponds to the function definition: z = (x + y)
    2. rename all variables in it adding suffix "_new": z = (x_new + y_new) 
        we do this to avoid name conflicts with the variables in the parent scope, 
        ideally should be handled a bit better
    3. create a new assign node that assigns the arguments of the function call to the new variables 
        (x_new, y_new) = (1, 2), 
    4. insert it before the function expansion: (x_new, y_new) = (1, 2); z = (x_new + y_new)
    """
    def renaming_fun(x):
        return x + "_new" #TODO better renaming

    # G = copy.deepcopy(G)
    G.refresh()
    node: ast.Call = G.ast_nodes[node_id]
    assert isinstance(node, ast.Call), f"Node {node} is not a function call"

    parent_id = G.get_parent(node_id)
    parent: ast.Assign = G.ast_nodes[parent_id]
    assert parent.value == node, f"Parent node {parent} is not the function call {node}"

    function_defs = [
        n for n in G.ast_nodes.values() if isinstance(n, ast.FunctionDef) and n.name == node.func.id and n.lineno < node.lineno
    ]

    assert len(function_defs) > 0, f"No function definition found for {node.func.id}"

    if len(function_defs) > 1:
        print(f"Warning: Multiple function definitions for {node.func.id}")

    
    func_def: ast.FunctionDef = rename_all_vars(function_defs[-1], renaming_fun)

    def rename(a: ast.AST):
        return rename_all_vars(a, renaming_fun)
    
    renamed_args = [ast.arg(arg=renaming_fun(x.arg), annotation=x.annotation) for x in func_def.args.args]

    # parent.value = copy.copy(func_def.body[-1].value)

    # new_vars = ast.Tuple(elts=[ast.Name(id=x.arg, ctx=ast.Store()) for x in renamed_args],) 
    # values = ast.Tuple(elts=node.args) 
    # assign_node = ast.Assign(targets=[new_vars], value=values)
    new_assign_node = get_assign_node(renamed_args, node.args)

    grandparent = G.ast_nodes[G.get_parent(parent_id)]
    assert hasattr(grandparent, 'body'), f"Grandparent node {grandparent} has no body"

    idx = grandparent.body.index(parent)
    # grandparent.body = grandparent.body[:idx] + [new_assign_node] + func_def.body[:-1] + [parent] + grandparent.body[idx+1:]
    ##################


    x = grandparent
    func_def: ast.FunctionDef = function_defs[-1]
    assign = parent     # == |Assign|(value=Call(func=func_name), targets=t)
    # renamed_args = [ast.arg(arg=renaming_fun(x.arg), annotation=x.annotation) for x in func_def.args.args]
    # creating new variables to represent variables from the func_def scope 
    new_vars = ast.Tuple(elts=[ast.Name(id=x.arg, ctx=ast.Store()) for x in rename(func_def).args.args]) 
    values = ast.Tuple(elts=node.args) 

    # assigning to the new variables values that were passed as function call arguments
    assign_new_vars = ast.Assign(targets=[new_vars], value=values)

    # changing the value of the original assignment from function call to its function AST
    # func_def.body[-1].value is the return of the function 

    assign.value = rename(func_def).body[-1].value 

    x.body = x.body[:idx]  + [assign_new_vars] + rename(func_def).body[:-1] + [assign] + x.body[idx+1:]

    G.refresh()



    return G


def extract_function(G: CodeGraph, parent_id: int, start: int, end: int):
    # G = copy.deepcopy(G)
    G.refresh()
    parent = G.ast_nodes[parent_id]
    assert hasattr(parent, 'body'), 'The node is not a function'
    assert start < end, 'The start index should be smaller than the end index'
    end_node = parent.body[end]

    all_vars = []
    for node_body in parent.body[start:end+1]:
        all_vars.extend([node for node in ast.walk(node_body) if isinstance(node, ast.Name)])

    all_vars_lookup = {var.id: [node for node in all_vars if node.id == var.id] for var in all_vars}

    args = [ast.arg(arg=var, annotation=None) for var, appearances in all_vars_lookup.items() if isinstance(appearances[0].ctx, ast.Load)]
    
    function_name = 'extracted_function' # TODO

    function_def = ast.FunctionDef(
        name=function_name, 
        args=ast.arguments(args=args, vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), 
        body=parent.body[start:end+1], 
        decorator_list=[]
    )

    call_node = ast.Call(
        func=ast.Name(id=function_name, ctx=G.load_node), 
        args=[ast.Name(id=arg.arg, ctx=G.load_node) for arg in args], 
        keywords=[]
        )

    match end_node.__class__:
        case ast.Assign:
            return_node = ast.Return(ast.Name(id=end_node.targets[0].id, ctx=G.load_node))
            function_def.body.append(return_node)
            call_node = ast.Assign(targets=[ast.Name(id=end_node.targets[0].id, ctx=G.store_node)], value=call_node)
        case ast.Call:
            pass
        case _:
            raise ValueError('The end node should be an assignment or a function call')
    
    parent.body = parent.body[:start] + [function_def, call_node] + parent.body[end+1:]
    G.refresh()
    return G

class RedundantVariableRemover(ast.NodeTransformer):
    def __init__(self, redundant_vars):
        self.redundant_vars = redundant_vars

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in self.redundant_vars:
                return None 
        return self.generic_visit(node)

def find_redundant_variables(G: CodeGraph):
    redundant_vars = set()
    for _, node in G.our_nodes.items():
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
    G.refresh()
    return G