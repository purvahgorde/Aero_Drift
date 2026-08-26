import json
from pathlib import Path

from app.graph.builder import build_cloud_graph
from app.graph.drift_detector import detect_public_database_exposure
from app.dashboard.summary import show_summary
from app.dashboard.topology_view import render_topology
from app.dashboard.audit import show_drift_findings


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MOCK_STATE_FILE = PROJECT_ROOT / "data" / "mock_aws_state.json"


def load_mock_state():
    """Load the local mock AWS infrastructure state."""
    with open(MOCK_STATE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    """Run the AeroDrift cloud audit pipeline."""

    print("\n=== AeroDrift Cloud Audit ===\n")

    # 1. Load current cloud state
    cloud_state = load_mock_state()

    # 2. Display infrastructure summary
    show_summary(cloud_state)

    # 3. Build NetworkX topology
    graph = build_cloud_graph(cloud_state)

    print()

    # 4. Display cloud topology
    render_topology(graph)

    print()

    # 5. Detect security drift
    findings = detect_public_database_exposure(graph)

    # 6. Display security audit
    show_drift_findings(findings)

    print()

    # 7. Final result
    if findings:
        print(
            f"AeroDrift detected {len(findings)} security "
            f"drift finding(s)."
        )
    else:
        print("AeroDrift detected no security drift.")


if __name__ == "__main__":
    main()