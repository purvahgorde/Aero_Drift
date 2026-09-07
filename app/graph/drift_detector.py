import networkx as nx


def detect_public_database_exposure(graph):
    """
    Detect database/instance resources that are reachable
    from the public Internet.
    """

    findings = []

    if "internet" not in graph:
        return findings

    for node, attributes in graph.nodes(data=True):

        if attributes.get("resource_type") != "instance":
            continue

        name = attributes.get("name", "").lower()

        # For our current project model, the database instance
        # is identified by its name.
        if "db" not in name and "database" not in name:
            continue

        if nx.has_path(graph, "internet", node):

            path = nx.shortest_path(
                graph,
                "internet",
                node,
            )

            security_groups = [
                resource
                for resource in path
                if graph.nodes[resource].get("resource_type")
                == "security_group"
            ]

            findings.append(
                {
                    "severity": "CRITICAL",
                    "resource_id": node,
                    "resource_name": attributes.get("name"),
                    "security_groups": security_groups,
                    "reason": "Public internet path detected to database",
                    "path": path,
                }
            )

    return findings