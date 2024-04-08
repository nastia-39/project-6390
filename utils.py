import ast
import json
import networkx as nx

def ast_to_networkx(node):
    G = nx.DiGraph()

    def traverse(node, parent=None):
        if parent is not None:
            G.add_edge(parent, id(node))

        attrs = {}
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                attrs[field] = [id(item) for item in value if isinstance(item, ast.AST)]
                for item in value:
                    if isinstance(item, ast.AST):
                        traverse(item, id(node))
            elif isinstance(value, ast.AST):
                attrs[field] = id(value)
                traverse(value, id(node))
            else:
                attrs[field] = value
            if 'name' in attrs:
                attrs['fun_name'] = attrs.pop('name')

        attrs['type'] = type(node).__name__
        # attrs['shape'] = 'box'
        # G.node("Python", style = 'filled', color = "red", shape = "box")
        
        G.nodes[id(node)].update(attrs)

    traverse(node)
    return G


def is_json_serializable(obj):
    try:
        json.dumps(obj)
        return True
    except (TypeError, OverflowError):
        return False
    
def node_ignore_ids(G, node):
    def helper(v):
        if v is None or v == []:
            return False
        if isinstance(v, list) and len(v) == 0:
            return False

        if isinstance(v, list) and len(v) >= 1:
            v = v[0]

        if isinstance(v, int):
            res = v not in G.nodes()
        else:
            res = True
        return res
    
    return {k: v for k, v in node.items() if helper(v)}

def node_transform(G, node_id):
    attrs = node_ignore_ids(G, G.nodes[node_id])
    if "size" in attrs:
        attrs.pop("size")
    return json.dumps(attrs, indent=2)[1:-1]