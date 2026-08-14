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

print("Nodes:", topology.graph.number_of_nodes())
print("Edges:", topology.graph.number_of_edges())

print("Node data:")

for node, data in topology.graph.nodes(data=True):
    print(node, data)



assert topology.graph.number_of_nodes() == 4
assert topology.graph.number_of_edges() == 0

assert "vpc-001" in topology.graph
assert "subnet-001" in topology.graph
assert "i-12345" in topology.graph
assert "db-001" in topology.graph

assert topology.graph.nodes["i-12345"]["resource_type"] == "EC2"
assert topology.graph.nodes["i-12345"]["name"] == "web-server"