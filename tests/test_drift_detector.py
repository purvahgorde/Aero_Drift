from app.graph.topology import CloudTopology
from app.graph.nodes import CloudNode
from app.detection.drift_detector import detect_drift


# -----------------------------
# Previous topology
# -----------------------------

previous = CloudTopology()

previous.add_node(
    CloudNode("vpc-001", "VPC", "main-vpc")
)

previous.add_node(
    CloudNode("subnet-001", "Subnet", "private-subnet")
)

previous.add_node(
    CloudNode("i-12345", "EC2", "web-server")
)

previous.add_relationship(
    "vpc-001",
    "subnet-001"
)

previous.add_relationship(
    "subnet-001",
    "i-12345"
)


# -----------------------------
# Current topology
# -----------------------------

current = CloudTopology()

current.add_node(
    CloudNode("vpc-001", "VPC", "main-vpc")
)

current.add_node(
    CloudNode("subnet-001", "Subnet", "private-subnet")
)

current.add_node(
    CloudNode("i-12345", "EC2", "web-server")
)

# New database
current.add_node(
    CloudNode("db-001", "Database", "private-db")
)

current.add_relationship(
    "vpc-001",
    "subnet-001"
)

current.add_relationship(
    "subnet-001",
    "i-12345"
)

# New relationship
current.add_relationship(
    "i-12345",
    "db-001"
)


# -----------------------------
# Detect drift
# -----------------------------

drift = detect_drift(
    previous,
    current
)

print("Drift:")
print(drift)