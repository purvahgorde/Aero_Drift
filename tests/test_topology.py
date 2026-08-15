from app.graph.topology import CloudTopology
from app.graph.nodes import CloudNode


topology = CloudTopology()


vpc = CloudNode(
    "vpc-001",
    "VPC",
    "main-vpc"
)

subnet = CloudNode(
    "subnet-001",
    "Subnet",
    "private-subnet"
)

ec2 = CloudNode(
    "i-12345",
    "EC2",
    "web-server"
)

database = CloudNode(
    "db-001",
    "Database",
    "private-db"
)


topology.add_node(vpc)
topology.add_node(subnet)
topology.add_node(ec2)
topology.add_node(database)


topology.add_relationship("vpc-001", "subnet-001")
topology.add_relationship("subnet-001", "i-12345")
topology.add_relationship("i-12345", "db-001")


print("Nodes:", topology.graph.number_of_nodes())
print("Edges:", topology.graph.number_of_edges())

print("Node data:")

for node, data in topology.graph.nodes(data=True):
    print(node, data)

print("Edges:")

for source, target in topology.graph.edges():
    print(source, "->", target)


assert topology.graph.number_of_nodes() == 4
assert topology.graph.number_of_edges() == 3

assert "vpc-001" in topology.graph
assert "subnet-001" in topology.graph
assert "i-12345" in topology.graph
assert "db-001" in topology.graph

assert topology.graph.nodes["i-12345"]["resource_type"] == "EC2"
assert topology.graph.nodes["i-12345"]["name"] == "web-server"

assert topology.graph.has_edge("vpc-001", "subnet-001")
assert topology.graph.has_edge("subnet-001", "i-12345")
assert topology.graph.has_edge("i-12345", "db-001")

assert not topology.graph.has_edge("subnet-001", "vpc-001")
assert not topology.graph.has_edge("i-12345", "subnet-001")
assert not topology.graph.has_edge("db-001", "i-12345")