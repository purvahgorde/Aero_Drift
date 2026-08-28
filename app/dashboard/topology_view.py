from rich.console import Console
from rich.tree import Tree

console = Console()

# Colour per resource type for visual distinction
_TYPE_COLORS = {
    "VPC": "bold cyan",
    "Subnet": "yellow",
    "EC2": "green",
    "SecurityGroup": "magenta",
}


def _label(resource_type, resource_id, name):
    """Build a Rich-formatted label like 'EC2: i-001 (web-server-1)'."""
    color = _TYPE_COLORS.get(resource_type, "white")
    label = f"[{color}]{resource_type}[/{color}]: {resource_id}"
    if name:
        label += f" ({name})"
    return label


def _add_children(parent_branch, nx_graph, node_id):
    """Recursively add child nodes to the tree branch."""
    for child_id in nx_graph.successors(node_id):
        child_data = nx_graph.nodes.get(child_id, {})
        child_type = child_data.get("resource_type") or child_data.get("type", "Resource")
        child_name = child_data.get("name")
        child_branch = parent_branch.add(_label(child_type, child_id, child_name))
        _add_children(child_branch, nx_graph, child_id)


def render_topology(graph):
    """Render the cloud topology graph as a rich tree view.

    Produces a nested hierarchy starting from root nodes (nodes with no
    incoming edges), e.g.:

        AeroDrift Cloud Topology
        VPC: vpc-001 (AeroDrift-VPC)
        ├── Subnet: subnet-001
        │   └── EC2: i-001 (web-server-1)
        │       └── SecurityGroup: sg-001 (web-sg)
        └── Subnet: subnet-002
            └── EC2: i-002 (db-server-1)
                └── SecurityGroup: sg-002 (db-sg)
    """
    nx_graph = graph.graph if hasattr(graph, "graph") else graph

    tree = Tree("[bold cyan]AeroDrift Cloud Topology[/bold cyan]")

    # Find root nodes – those with no incoming edges
    roots = [n for n in nx_graph.nodes() if nx_graph.in_degree(n) == 0]

    for root_id in roots:
        root_data = nx_graph.nodes.get(root_id, {})
        root_type = root_data.get("resource_type") or root_data.get("type", "Resource")
        root_name = root_data.get("name")
        root_branch = tree.add(_label(root_type, root_id, root_name))
        _add_children(root_branch, nx_graph, root_id)

    console.print(tree)