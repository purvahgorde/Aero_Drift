def generate_remediation_suggestions(drift):
    """
    Generate remediation suggestions based on detected drift.
    This function only suggests actions.
    It does not modify AWS resources.
    """

    suggestions = []

    # Changed nodes
    changed_nodes = drift.get("nodes", {}).get("changed", [])

    for node in changed_nodes:

        resource_id = node.get("resource_id")
        changes = node.get("changes", {})

        for attribute, values in changes.items():

            previous_value = values.get("previous")
            current_value = values.get("current")

            if attribute == "state":

                suggestions.append({
                    "resource_id": resource_id,
                    "action": "Review resource state",
                    "reason": (
                        f"State changed from "
                        f"{previous_value} to {current_value}"
                    ),
                    "recommendation": (
                        "Check whether the new state is expected."
                    )
                })

            elif attribute == "subnet_id":

                suggestions.append({
                    "resource_id": resource_id,
                    "action": "Review subnet configuration",
                    "reason": (
                        f"Subnet changed from "
                        f"{previous_value} to {current_value}"
                    ),
                    "recommendation": (
                        "Verify that the resource is connected "
                        "to the correct subnet."
                    )
                })

            elif attribute == "name":

                suggestions.append({
                    "resource_id": resource_id,
                    "action": "Review resource name",
                    "reason": (
                        f"Name changed from "
                        f"{previous_value} to {current_value}"
                    ),
                    "recommendation": (
                        "Verify that the new resource name "
                        "is correct."
                    )
                })

            else:

                suggestions.append({
                    "resource_id": resource_id,
                    "action": f"Review {attribute}",
                    "reason": (
                        f"{attribute} changed from "
                        f"{previous_value} to {current_value}"
                    ),
                    "recommendation": (
                        f"Verify the {attribute} configuration."
                    )
                })

    # Added nodes
    added_nodes = drift.get("nodes", {}).get("added", [])

    for resource_id in added_nodes:

        suggestions.append({
            "resource_id": resource_id,
            "action": "Review newly added resource",
            "reason": "A new cloud resource was detected.",
            "recommendation": (
                "Verify that this resource was intentionally created."
            )
        })

    # Removed nodes
    removed_nodes = drift.get("nodes", {}).get("removed", [])

    for resource_id in removed_nodes:

        suggestions.append({
            "resource_id": resource_id,
            "action": "Review removed resource",
            "reason": "A cloud resource was removed.",
            "recommendation": (
                "Verify that the resource was intentionally deleted."
            )
        })

    # Added relationships
    added_relationships = (
        drift.get("relationships", {}).get("added", [])
    )

    for source_id, target_id in added_relationships:

        suggestions.append({
            "resource_id": source_id,
            "action": "Review new relationship",
            "reason": (
                f"New relationship detected: "
                f"{source_id} -> {target_id}"
            ),
            "recommendation": (
                "Verify that this connection is expected."
            )
        })

    # Removed relationships
    removed_relationships = (
        drift.get("relationships", {}).get("removed", [])
    )

    for source_id, target_id in removed_relationships:

        suggestions.append({
            "resource_id": source_id,
            "action": "Review removed relationship",
            "reason": (
                f"Relationship removed: "
                f"{source_id} -> {target_id}"
            ),
            "recommendation": (
                "Verify that removing this connection "
                "does not break dependencies."
            )
        })

    return suggestions