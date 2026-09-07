from app.graph.topology import create_network_graph


resources = {
    "vpcs": [
        {
            "id": "vpc-001",
            "tags": [
                {
                    "Key": "Name",
                    "Value": "main-vpc"
                }
            ]
        }
    ],

    "subnets": [
        {
            "id": "subnet-001",
            "vpc_id": "vpc-001"
        }
    ],

    "instances": [
        {
            "id": "i-12345",
            "subnet_id": "subnet-001",
            "vpc_id": "vpc-001",
            "security_group_ids": ["sg-001"]
        }
    ],

    "security_groups": [
        {
            "id": "sg-001",
            "vpc_id": "vpc-001",
            "name": "web-sg",
            "ingress_rules": [],
            "egress_rules": []
        }
    ]
}


topology = create_network_graph(resources)


print("Nodes:")
for node, data in topology.get_nodes():
    print(node, data)


print("\nEdges:")
for source, target in topology.get_edges():
    print(source, "->", target)


print("\nGraph summary:")
print(topology.get_graph_summary())


assert "vpc-001" in topology.graph
assert "subnet-001" in topology.graph
assert "i-12345" in topology.graph
assert "sg-001" in topology.graph


assert topology.graph.has_edge(
    "vpc-001",
    "subnet-001"
)

assert topology.graph.has_edge(
    "subnet-001",
    "i-12345"
)

assert topology.graph.has_edge(
    "i-12345",
    "sg-001"
)

assert topology.graph.nodes["sg-001"]["resource_type"] == "SecurityGroup"


print("\nDay 6 test passed!")