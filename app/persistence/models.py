"""State comparison and configuration drift detection for AeroDrift.

Compares resource states between two scans persisted in the SQLite database
and produces a structured drift result that the CLI can consume.

This module operates on the serialised resource rows returned by
``AeroDriftDB.get_resources_for_scan`` — it does **not** reimplement the
existing ``detection.drift_detector`` topology-level comparison.  Instead it
focuses on *resource-level* configuration drift derived from persisted state.
"""

import json


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compare_scans(previous_resources, current_resources):
    """Compare resource states between two scans.

    Parameters
    ----------
    previous_resources : list[dict]
        Resource rows from the previous scan (each row has
        ``resource_id``, ``resource_type``, ``resource_name``,
        ``resource_state``).
    current_resources : list[dict]
        Resource rows from the current scan.

    Returns
    -------
    dict
        A drift result with keys::

            {
                "added":    [resource_id, ...],
                "removed":  [resource_id, ...],
                "modified": [
                    {
                        "resource_id": str,
                        "resource_type": str,
                        "changes": {
                            field: {"previous": ..., "current": ...},
                            ...
                        },
                    },
                    ...
                ],
                "unchanged": [resource_id, ...],
                "total_changes": int,
            }
    """
    prev_map = _build_resource_map(previous_resources)
    curr_map = _build_resource_map(current_resources)

    prev_ids = set(prev_map.keys())
    curr_ids = set(curr_map.keys())

    added = sorted(curr_ids - prev_ids)
    removed = sorted(prev_ids - curr_ids)
    common = prev_ids & curr_ids

    modified = []
    unchanged = []

    for rid in sorted(common):
        prev_state = prev_map[rid]["parsed_state"]
        curr_state = curr_map[rid]["parsed_state"]

        changes = _diff_states(prev_state, curr_state)
        if changes:
            modified.append({
                "resource_id": rid,
                "resource_type": curr_map[rid]["resource_type"],
                "changes": changes,
            })
        else:
            unchanged.append(rid)

    total_changes = len(added) + len(removed) + len(modified)

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged": unchanged,
        "total_changes": total_changes,
    }


def build_drift_summary(drift_result):
    """Build a human-readable drift summary dict for the CLI.

    Parameters
    ----------
    drift_result : dict
        Output of :func:`compare_scans`.

    Returns
    -------
    dict
        Summary with keys ``status``, ``added_count``, ``removed_count``,
        ``modified_count``, ``unchanged_count``, ``total_changes``,
        ``details`` (list of detail dicts).
    """
    if drift_result["total_changes"] == 0:
        status = "NO_DRIFT"
    else:
        status = "DRIFT_DETECTED"

    details = []

    for rid in drift_result["added"]:
        details.append({
            "change_type": "ADDED",
            "resource_id": rid,
            "description": "New resource detected",
        })

    for rid in drift_result["removed"]:
        details.append({
            "change_type": "REMOVED",
            "resource_id": rid,
            "description": "Resource no longer present",
        })

    for mod in drift_result["modified"]:
        change_lines = []
        for field, vals in mod["changes"].items():
            prev_val = _format_value(vals["previous"])
            curr_val = _format_value(vals["current"])
            change_lines.append(f"{field}: {prev_val} -> {curr_val}")
        details.append({
            "change_type": "MODIFIED",
            "resource_id": mod["resource_id"],
            "resource_type": mod.get("resource_type", ""),
            "description": "; ".join(change_lines),
            "changes": mod["changes"],
        })

    return {
        "status": status,
        "added_count": len(drift_result["added"]),
        "removed_count": len(drift_result["removed"]),
        "modified_count": len(drift_result["modified"]),
        "unchanged_count": len(drift_result["unchanged"]),
        "total_changes": drift_result["total_changes"],
        "details": details,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Fields that are not meaningful for configuration drift comparison.
_IGNORED_FIELDS = frozenset()


def _build_resource_map(resource_rows):
    """Index resource rows by ``resource_id`` and parse the JSON state."""
    mapping = {}
    for row in resource_rows:
        rid = row["resource_id"]
        try:
            parsed = json.loads(row["resource_state"])
        except (json.JSONDecodeError, TypeError):
            parsed = {}
        mapping[rid] = {
            "resource_type": row.get("resource_type", ""),
            "resource_name": row.get("resource_name", ""),
            "parsed_state": parsed,
        }
    return mapping


def _diff_states(prev_state, curr_state):
    """Compare two parsed state dicts and return changed fields.

    Returns a dict of ``{field: {"previous": ..., "current": ...}}``
    for every field whose value changed.  Returns an empty dict if no
    meaningful changes are found.
    """
    changes = {}
    all_keys = set(prev_state.keys()) | set(curr_state.keys())

    for key in all_keys:
        if key in _IGNORED_FIELDS:
            continue
        prev_val = prev_state.get(key)
        curr_val = curr_state.get(key)
        if prev_val != curr_val:
            changes[key] = {"previous": prev_val, "current": curr_val}

    return changes


def _format_value(val):
    """Format a value for human-readable display."""
    if val is None:
        return "<none>"
    if isinstance(val, (list, dict)):
        return json.dumps(val, default=str)
    return str(val)
