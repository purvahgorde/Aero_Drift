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
                node_data = topology.graph.nodes.get(source_id, {})

                if node_data.get("resource_type") == "EC2":
                    exposed_instances.append(source_id)

    return exposed_instances