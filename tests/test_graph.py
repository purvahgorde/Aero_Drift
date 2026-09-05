import json
import networkx as nx

from app.graph.builder import build_cloud_graph
from app.graph.drift_detector import detect_public_database_exposure


def load_mock_state():
    with open("data/mock_aws_state.json", "r") as file:
        return json.load(file)


def test_cloud_graph_contains_expected_nodes():
    cloud_state = load_mock_state()

    graph = build_cloud_graph(cloud_state)

    assert graph.number_of_nodes() == 8

    assert "internet" in graph
    assert "vpc-001" in graph
    assert "subnet-001" in graph
    assert "subnet-002" in graph
    assert "sg-001" in graph
    assert "sg-002" in graph
    assert "i-001" in graph
    assert "i-002" in graph


def test_cloud_graph_contains_expected_relationships():
    cloud_state = load_mock_state()

    graph = build_cloud_graph(cloud_state)

    assert graph.has_edge("vpc-001", "subnet-001")
    assert graph.has_edge("vpc-001", "subnet-002")

    assert graph.has_edge("vpc-001", "sg-001")
    assert graph.has_edge("vpc-001", "sg-002")

    assert graph.has_edge("subnet-001", "i-001")
    assert graph.has_edge("subnet-002", "i-002")

    assert graph.has_edge("sg-001", "i-001")
    assert graph.has_edge("sg-002", "i-002")

    assert graph.has_edge("internet", "sg-001")
    assert graph.has_edge("internet", "sg-002")


def test_cloud_graph_has_correct_resource_types():
    cloud_state = load_mock_state()

    graph = build_cloud_graph(cloud_state)

    assert graph.nodes["internet"]["resource_type"] == "internet"
    assert graph.nodes["vpc-001"]["resource_type"] == "vpc"
    assert graph.nodes["subnet-001"]["resource_type"] == "subnet"
    assert graph.nodes["sg-002"]["resource_type"] == "security_group"
    assert graph.nodes["i-002"]["resource_type"] == "instance"


def test_public_path_to_database_exists():
    cloud_state = load_mock_state()

    graph = build_cloud_graph(cloud_state)

    assert nx.has_path(graph, "internet", "i-002")


def test_public_path_to_database_is_expected():
    cloud_state = load_mock_state()

    graph = build_cloud_graph(cloud_state)

    path = nx.shortest_path(graph, "internet", "i-002")

    assert path == [
        "internet",
        "sg-002",
        "i-002",
    ]

def test_drift_detector_finds_public_database():
    cloud_state = load_mock_state()

    graph = build_cloud_graph(cloud_state)

    findings = detect_public_database_exposure(graph)

    assert len(findings) == 1

    finding = findings[0]

    assert finding["severity"] == "CRITICAL"
    assert finding["resource_id"] == "i-002"
    assert finding["resource_name"] == "db-server-1"
    assert finding["security_groups"] == ["sg-002"]

    assert finding["path"] == [
        "internet",
        "sg-002",
        "i-002",
    ]


def test_drift_detector_returns_no_finding_for_private_database():
    cloud_state = load_mock_state()

    # Remove the public ingress rule from the database security group.
    for security_group in cloud_state["security_groups"]:
        if security_group["id"] == "sg-002":
            security_group["ingress_rules"] = []

    graph = build_cloud_graph(cloud_state)

    findings = detect_public_database_exposure(graph)

    assert findings == []






def test_end_to_end_cloud_audit_detects_public_database():
    import json
    from pathlib import Path

    from app.graph.builder import build_cloud_graph
    from app.graph.drift_detector import detect_public_database_exposure

    mock_file = Path("data/mock_aws_state.json")

    with mock_file.open("r", encoding="utf-8") as file:
        cloud_state = json.load(file)

    graph = build_cloud_graph(cloud_state)

    findings = detect_public_database_exposure(graph)

    assert len(findings) == 1
    assert findings[0]["severity"] == "CRITICAL"
    assert findings[0]["resource_id"] == "i-002"