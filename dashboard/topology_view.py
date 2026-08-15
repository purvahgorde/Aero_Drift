from rich.console import Console
from rich.tree import Tree

console = Console()

def render_topology(graph):
    tree = Tree("[bold cyan]AeroDrift Cloud Topology[/bold cyan]")

    for node, data in graph.nodes(data=True):
        resource_type = data.get("type", "resource")

        branch = tree.add(
            f"[yellow]{resource_type}[/yellow]: {node}"
        )

        for target in graph.successors(node):
            target_data = graph.nodes[target]
            target_type = target_data.get("type", "resource")

            branch.add(
                f"[green]{target_type}[/green]: {target}"
            )

    console.print(tree)