from app.remediation.remediation import generate_remediation_suggestions


# Test added resource
added_resource_drift = {
    "nodes": {
        "added": ["db-002"],
        "removed": [],
        "changed": []
    },
    "relationships": {
        "added": [],
        "removed": []
    }
}

added_suggestions = generate_remediation_suggestions(
    added_resource_drift
)

print("Remediation Suggestions:")
for suggestion in added_suggestions:
    print(suggestion)

assert len(added_suggestions) == 1
assert added_suggestions[0]["resource_id"] == "db-002"

print("Added resource remediation test passed!")



from app.graph.topology import CloudTopology
from app.graph.nodes import CloudNode
from app.detection.drift_detector import detect_drift
from app.remediation.remediation import generate_remediation_suggestions


# ==========================================
# WEEK 4 DAY 2 - DRIFT + REMEDIATION TEST
# ==========================================

previous = CloudTopology()

previous.add_node(
    CloudNode(
        "i-12345",
        "EC2",
        "web-server"
    )
)

previous.graph.nodes["i-12345"]["state"] = "running"
previous.graph.nodes["i-12345"]["subnet_id"] = "subnet-001"


current = CloudTopology()

current.add_node(
    CloudNode(
        "i-12345",
        "EC2",
        "production-server"
    )
)

current.graph.nodes["i-12345"]["state"] = "stopped"
current.graph.nodes["i-12345"]["subnet_id"] = "subnet-002"


# ==========================================
# STEP 1: DETECT DRIFT
# ==========================================

drift = detect_drift(
    previous,
    current
)

print("Detected Drift:")
print(drift)


assert len(drift["nodes"]["changed"]) == 1


# ==========================================
# STEP 2: GENERATE REMEDIATION
# ==========================================

suggestions = generate_remediation_suggestions(
    drift
)

print("Remediation Suggestions:")
for suggestion in suggestions:
    print(suggestion)


# ==========================================
# VERIFY
# ==========================================

assert len(suggestions) == 3

print("Week 4 Day 2 integration test passed!")