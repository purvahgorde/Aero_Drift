def detect_node_changes(previous_topology, current_topology):
    """
    Compare nodes between previous and current topology.
    """
    previous_nodes = set(previous_topology.graph.nodes())
    current_nodes = set(current_topology.graph.nodes())

    added_nodes = current_nodes - previous_nodes
    removed_nodes = previous_nodes - current_nodes

    return {
        "added": list(added_nodes),
        "removed": list(removed_nodes)
    }


def detect_relationship_changes(previous_topology, current_topology):
    """
    Compare relationships between previous and current topology.
    """
    previous_edges = set(previous_topology.graph.edges())
    current_edges = set(current_topology.graph.edges())

    added_edges = current_edges - previous_edges
    removed_edges = previous_edges - current_edges

    return {
        "added": list(added_edges),
        "removed": list(removed_edges)
    }


def detect_drift(previous_topology, current_topology):
    """
    Detect changes between previous and current cloud topology.
    """

    node_changes = detect_node_changes(
        previous_topology,
        current_topology
    )

    relationship_changes = detect_relationship_changes(
        previous_topology,
        current_topology
    )

    return {
        "nodes": node_changes,
        "relationships": relationship_changes
    }