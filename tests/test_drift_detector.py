from app.graph.topology import CloudTopology
from app.graph.nodes import CloudNode
from app.detection.drift_detector import detect_drift


# ==========================================
# PREVIOUS TOPOLOGY
# ==========================================

previous = CloudTopology()

previous.add_node(
    CloudNode(
        "vpc-001",
        "VPC",
        "main-vpc"
    )
)

previous.add_node(
    CloudNode(
        "subnet-001",
        "Subnet",
        "private-subnet"
    )
)

previous.add_node(
    CloudNode(
        "i-12345",
        "EC2",
        "web-server"
    )
)

previous.add_relationship(
    "vpc-001",
    "subnet-001"
)

previous.add_relationship(
    "subnet-001",
    "i-12345"
)


# ==========================================
# CURRENT TOPOLOGY
# ==========================================

current = CloudTopology()

current.add_node(
    CloudNode(
        "vpc-001",
        "VPC",
        "main-vpc"
    )
)

current.add_node(
    CloudNode(
        "subnet-001",
        "Subnet",
        "private-subnet"
    )
)

# Same EC2 ID but name has changed
current.add_node(
    CloudNode(
        "i-12345",
        "EC2",
        "production-server"
    )
)

current.add_relationship(
    "vpc-001",
    "subnet-001"
)

current.add_relationship(
    "subnet-001",
    "i-12345"
)


# ==========================================
# DETECT DRIFT
# ==========================================

drift = detect_drift(
    previous,
    current
)

print("Drift:")
print(drift)


# ==========================================
# VERIFY RESULT
# ==========================================

assert "i-12345" not in drift["nodes"]["added"]

assert "i-12345" not in drift["nodes"]["removed"]

assert len(drift["nodes"]["changed"]) == 1

changed = drift["nodes"]["changed"][0]

assert changed["resource_id"] == "i-12345"

assert changed["changes"]["name"]["previous"] == "web-server"

assert changed["changes"]["name"]["current"] == "production-server"


print("Day 2 test passed!")