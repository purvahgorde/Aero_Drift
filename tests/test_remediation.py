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