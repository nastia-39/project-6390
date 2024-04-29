import ast
import networkx as nx
import torch_geometric.nn as pyg_nn
import torch
from torch_geometric.utils.convert import from_networkx

code = """
def main():
    def plus(a, b):
        return a + b
    
    x, y = 1, 2
    res = plus(x, y)
    return res
"""

def ast_to_networkx(tree):
    """
    Converts an AST to a NetworkX graph.

    Args:
        tree: The AST to convert.

    Returns:
        A NetworkX graph.
    """

    graph = nx.DiGraph()

    # Create a node for the root of the tree.
    root_node = graph.add_node(id(tree), label=type(tree).__name__)

    # Recursively add nodes for the children of the root node.
    _add_nodes(graph, id(tree), tree)

    return graph

def _add_nodes(graph, parent_node, node):
    """
    Recursively adds nodes for the children of a given node.

    Args:
        graph: The NetworkX graph.
        parent_node: The node to which the new nodes will be added.
        node: The node whose children will be added.
    """

    # Create a node for the current node.
    node_id = id(node)
    graph.add_node(node_id, label=type(node).__name__)

    # Add an edge between the parent node and the current node.
    graph.add_edge(parent_node, node_id)

    # Recursively add nodes for the children of the current node.
    for child in ast.iter_child_nodes(node):
        _add_nodes(graph, node_id, child)

class GraphConvModel(pyg_nn.MessagePassing):
    def __init__(self, emb_dim):
        super(GraphConvModel, self).__init__(aggr='add')

        self.linear = torch.nn.Linear(emb_dim, emb_dim)

    def forward(self, x, edge_index):
        # x has shape [N, in_channels]
        # edge_index has shape [2, E]

        # Perform message passing.
        x = self.propagate(edge_index, x=x)

        # Apply a linear transformation to the node features.
        x = self.linear(x)

        return x

    def message(self, x_j, edge_index, index):
        # x_j has shape [E, in_channels]

        # Return the message to be passed to the target nodes.
        return x_j

# Parse code as AST and convert to Networkx
tree = ast.parse(code)
networkx_tree = ast_to_networkx(tree)

# print(ast.dump(tree))

# Convert NetworkX graph to PyTorch Geometric Data object
data = from_networkx(networkx_tree)
data.x = torch.randn((data.num_nodes, 32))

# Create a GraphConvModel instance.
model = GraphConvModel(emb_dim=32)

# Perform graph embedding.
x = model(data.x, data.edge_index)

# Print the node embeddings.
print(x)

