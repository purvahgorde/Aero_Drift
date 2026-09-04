from app.graph.topology import CloudTopology
from app.graph.nodes import CloudNode
from app.detection.drift_detector import detect_drift


# ==========================================
# PREVIOUS TOPOLOGY
# ==========================================

previous = CloudTopology()

previous.add_node(
    CloudNode(
        "i-12345",
        "EC2",
        "web-server"
    )
)

# Add extra configuration information
previous.graph.nodes["i-12345"]["state"] = "running"
previous.graph.nodes["i-12345"]["subnet_id"] = "subnet-001"


# ==========================================
# CURRENT TOPOLOGY
# ==========================================

current = CloudTopology()

current.add_node(
    CloudNode(
        "i-12345",
        "EC2",
        "production-server"
    )
)

# Configuration has changed
current.graph.nodes["i-12345"]["state"] = "stopped"
current.graph.nodes["i-12345"]["subnet_id"] = "subnet-002"


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
# VERIFY
# ==========================================

assert len(drift["nodes"]["changed"]) == 1

changed = drift["nodes"]["changed"][0]

assert changed["resource_id"] == "i-12345"

assert changed["changes"]["name"]["previous"] == "web-server"

assert changed["changes"]["name"]["current"] == "production-server"

assert changed["changes"]["state"]["previous"] == "running"

assert changed["changes"]["state"]["current"] == "stopped"

assert changed["changes"]["subnet_id"]["previous"] == "subnet-001"

assert changed["changes"]["subnet_id"]["current"] == "subnet-002"


print("Day 3 test passed!")

# ==========================================
# WEEK 4 DAY 1 - NO DRIFT TEST
# ==========================================

previous_no_drift = CloudTopology()

previous_no_drift.add_node(
    CloudNode(
        "i-12345",
        "EC2",
        "web-server"
    )
)

previous_no_drift.graph.nodes["i-12345"]["state"] = "running"
previous_no_drift.graph.nodes["i-12345"]["subnet_id"] = "subnet-001"


current_no_drift = CloudTopology()

current_no_drift.add_node(
    CloudNode(
        "i-12345",
        "EC2",
        "web-server"
    )
)

current_no_drift.graph.nodes["i-12345"]["state"] = "running"
current_no_drift.graph.nodes["i-12345"]["subnet_id"] = "subnet-001"


# ==========================================
# DETECT DRIFT
# ==========================================

no_drift = detect_drift(
    previous_no_drift,
    current_no_drift
)

print("No Drift:")
print(no_drift)


# ==========================================
# VERIFY
# ==========================================

assert no_drift["nodes"]["added"] == []

assert no_drift["nodes"]["removed"] == []

assert no_drift["nodes"]["changed"] == []

assert no_drift["relationships"]["added"] == []

assert no_drift["relationships"]["removed"] == []


print("Week 4 Day 1 no-drift test passed!")