def detect_node_changes(previous_topology, current_topology):
    """
    Compare nodes between previous and current topology.

    Detects:
    1. Added nodes
    2. Removed nodes
    3. Changed node attributes
    """

    previous_nodes = set(previous_topology.graph.nodes())
    current_nodes = set(current_topology.graph.nodes())

    added_nodes = current_nodes - previous_nodes
    removed_nodes = previous_nodes - current_nodes

    changed_nodes = []

    # Check nodes that exist in both topologies
    common_nodes = previous_nodes & current_nodes

    for node_id in common_nodes:

        previous_data = previous_topology.graph.nodes[node_id]
        current_data = current_topology.graph.nodes[node_id]

        changes = {}

        # Compare resource type
        if previous_data.get("resource_type") != current_data.get("resource_type"):
            changes["resource_type"] = {
                "previous": previous_data.get("resource_type"),
                "current": current_data.get("resource_type")
            }

        # Compare name
        if previous_data.get("name") != current_data.get("name"):
            changes["name"] = {
                "previous": previous_data.get("name"),
                "current": current_data.get("name")
            }

        if changes:
            changed_nodes.append({
                "resource_id": node_id,
                "changes": changes
            })

    return {
        "added": list(added_nodes),
        "removed": list(removed_nodes),
        "changed": changed_nodes
    }


def detect_relationship_changes(previous_topology, current_topology):
    """
    Compare relationships between previous and current topology.

    Detects:
    1. Added relationships
    2. Removed relationships
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
    Detect all infrastructure drift between
    previous and current topology.
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