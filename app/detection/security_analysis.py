def allows_public_ingress(security_group):
    """
    Check whether a security group allows inbound traffic
    from the entire IPv4 Internet (0.0.0.0/0).
    """

    ingress_rules = security_group.get("ingress_rules", [])

    for rule in ingress_rules:
        for ip_range in rule.get("IpRanges", []):
            if ip_range.get("CidrIp") == "0.0.0.0/0":
                return True

    return False


def get_publicly_exposed_instances(topology, security_groups):
    """
    Find EC2 instances connected to Security Groups
    that allow public ingress.
    """

    exposed_instances = []

    for security_group in security_groups:

        if not allows_public_ingress(security_group):
            continue

        security_group_id = security_group.get("id")

        if not security_group_id:
            continue

        for source_id, target_id in topology.get_edges():

            if target_id == security_group_id:

                node_data = topology.graph.nodes.get(
                    source_id,
                    {}
                )

                if node_data.get("resource_type") == "EC2":
                    exposed_instances.append(source_id)

    return exposed_instances


def find_database_paths(topology, exposed_instances):
    """
    Find database paths from publicly exposed EC2 instances.
    """

    database_paths = []

    for instance_id in exposed_instances:

        for node_id, node_data in topology.get_nodes():

            if node_data.get("resource_type") != "Database":
                continue

            path = topology.find_path(
                instance_id,
                node_id
            )

            if path:
                database_paths.append({
                    "instance_id": instance_id,
                    "database_id": node_id,
                    "path": path
                })

    return database_paths


def detect_security_findings(topology, resources):
    """
    Detect high-risk cloud security findings.

    A finding is generated when:
    1. An EC2 instance is publicly exposed.
    2. That EC2 instance has a path to a database.
    """

    # Get the actual Security Group list from resources.
    security_groups = resources.get(
        "security_groups",
        []
    )

    # Find EC2 instances connected to public Security Groups.
    exposed_instances = get_publicly_exposed_instances(
        topology,
        security_groups
    )

    # Find database paths from those exposed EC2 instances.
    database_paths = find_database_paths(
        topology,
        exposed_instances
    )

    findings = []

    for database_path in database_paths:

        finding = {
            "severity": "HIGH",
            "instance_id": database_path["instance_id"],
            "database_id": database_path["database_id"],
            "path": database_path["path"],
            "reason": (
                "Publicly exposed EC2 instance has "
                "a path to a database"
            )
        }

        findings.append(finding)

    return findings