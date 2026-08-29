import networkx as nx


INTERNET_NODE = "internet"


def build_cloud_graph(cloud_state):
    """
    Build a directed NetworkX graph from collected AWS cloud state.

    Nodes represent AWS resources.
    Edges represent relationships and network pathways.
    """

    graph = nx.DiGraph()

    # -------------------------
    # Internet node
    # -------------------------
    graph.add_node(
        INTERNET_NODE,
        resource_type="internet",
        cidr="0.0.0.0/0",
    )

    # -------------------------
    # VPC nodes
    # -------------------------
    for vpc in cloud_state.get("vpcs", []):
        vpc_id = vpc["id"]

        graph.add_node(
            vpc_id,
            resource_type="vpc",
            cidr=vpc.get("cidr"),
            state=vpc.get("state"),
        )

    # -------------------------
    # Subnet nodes
    # -------------------------
    for subnet in cloud_state.get("subnets", []):
        subnet_id = subnet["id"]

        graph.add_node(
            subnet_id,
            resource_type="subnet",
            cidr=subnet.get("cidr"),
            availability_zone=subnet.get("availability_zone"),
        )

        vpc_id = subnet.get("vpc_id")

        if vpc_id:
            graph.add_edge(
                vpc_id,
                subnet_id,
                relationship="contains",
            )

    # -------------------------
    # Security Group nodes
    # -------------------------
    for security_group in cloud_state.get("security_groups", []):
        sg_id = security_group["id"]

        graph.add_node(
            sg_id,
            resource_type="security_group",
            name=security_group.get("name"),
            description=security_group.get("description"),
        )

        vpc_id = security_group.get("vpc_id")

        if vpc_id:
            graph.add_edge(
                vpc_id,
                sg_id,
                relationship="contains",
            )

        # -------------------------
        # Security Group ingress
        # -------------------------
        for rule in security_group.get("ingress_rules", []):
            source = rule.get("source")

            if source == "0.0.0.0/0":
                graph.add_edge(
                    INTERNET_NODE,
                    sg_id,
                    relationship="ingress",
                    protocol=rule.get("protocol"),
                    from_port=rule.get("from_port"),
                    to_port=rule.get("to_port"),
                    source=source,
                )

    # -------------------------
    # EC2 / Database nodes
    # -------------------------
    for instance in cloud_state.get("instances", []):
        instance_id = instance["id"]

        graph.add_node(
            instance_id,
            resource_type="instance",
            name=instance.get("name"),
            state=instance.get("state"),
        )

        subnet_id = instance.get("subnet_id")

        if subnet_id:
            graph.add_edge(
                subnet_id,
                instance_id,
                relationship="contains",
            )

        # EC2 instance → Security Group
        for sg_id in instance.get("security_group_ids", []):
            if sg_id in graph:
                graph.add_edge(
                    sg_id,
                    instance_id,
                    relationship="protects",
                )

    return graph