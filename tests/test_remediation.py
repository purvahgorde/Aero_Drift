from app.remediation.remediation import generate_remediation_suggestions


drift = {
    "nodes": {
        "added": [],
        "removed": [],
        "changed": [
            {
                "resource_id": "i-12345",
                "changes": {
                    "name": {
                        "previous": "web-server",
                        "current": "production-server"
                    },
                    "state": {
                        "previous": "running",
                        "current": "stopped"
                    },
                    "subnet_id": {
                        "previous": "subnet-001",
                        "current": "subnet-002"
                    }
                }
            }
        ]
    },
    "relationships": {
        "added": [],
        "removed": []
    }
}


suggestions = generate_remediation_suggestions(drift)


print("Remediation Suggestions:")

for suggestion in suggestions:
    print(suggestion)


assert len(suggestions) == 3

assert any(
    s["action"] == "Review resource state"
    for s in suggestions
)

assert any(
    s["action"] == "Review subnet configuration"
    for s in suggestions
)

assert any(
    s["action"] == "Review resource name"
    for s in suggestions
)


print("Day 4 test passed!")