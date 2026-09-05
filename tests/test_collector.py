import json
from pathlib import Path

from app.ingestion.collector import collect_aws_state
from app.graph.builder import build_cloud_graph


def test_collect_aws_state_returns_vpcs_and_instances():
    state = collect_aws_state()

    assert "vpcs" in state
    assert "instances" in state

    assert len(state["vpcs"]) > 0
    assert len(state["instances"]) > 0


def test_mock_aws_state_contains_expected_resources():
    mock_file = Path("data/mock_aws_state.json")

    with mock_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert len(data["vpcs"]) == 1
    assert len(data["subnets"]) == 2
    assert len(data["instances"]) == 2
    assert len(data["security_groups"]) == 2


def test_ec2_instances_have_relationships():
    state = collect_aws_state()

    for instance in state["instances"]:
        assert "id" in instance
        assert "vpc_id" in instance
        assert "subnet_id" in instance
        assert "security_group_ids" in instance


def test_mock_resources_have_required_relationship_fields():
    mock_file = Path("data/mock_aws_state.json")

    with mock_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    for subnet in data["subnets"]:
        assert "id" in subnet
        assert "vpc_id" in subnet
        assert "cidr" in subnet

    for security_group in data["security_groups"]:
        assert "id" in security_group
        assert "vpc_id" in security_group
        assert "ingress_rules" in security_group


def test_instance_relationship_ids_match_mock_resources():
    mock_file = Path("data/mock_aws_state.json")

    with mock_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    subnet_ids = {subnet["id"] for subnet in data["subnets"]}
    security_group_ids = {
        security_group["id"]
        for security_group in data["security_groups"]
    }

    for instance in data["instances"]:
        assert instance["subnet_id"] in subnet_ids

        for security_group_id in instance["security_group_ids"]:
            assert security_group_id in security_group_ids


def test_mock_vpc_relationships_are_consistent():
    mock_file = Path("data/mock_aws_state.json")

    with mock_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    vpc_ids = {vpc["id"] for vpc in data["vpcs"]}

    for subnet in data["subnets"]:
        assert subnet["vpc_id"] in vpc_ids

    for security_group in data["security_groups"]:
        assert security_group["vpc_id"] in vpc_ids

    for instance in data["instances"]:
        assert instance["vpc_id"] in vpc_ids


def test_mock_aws_state_flows_into_cloud_graph():
    mock_file = Path("data/mock_aws_state.json")

    with mock_file.open("r", encoding="utf-8") as file:
        cloud_state = json.load(file)

    graph = build_cloud_graph(cloud_state)

    assert "internet" in graph

    for vpc in cloud_state["vpcs"]:
        assert vpc["id"] in graph

    for subnet in cloud_state["subnets"]:
        assert subnet["id"] in graph

    for instance in cloud_state["instances"]:
        assert instance["id"] in graph

    for security_group in cloud_state["security_groups"]:
        assert security_group["id"] in graph


def test_cloud_graph_preserves_resource_relationships():
    mock_file = Path("data/mock_aws_state.json")

    with mock_file.open("r", encoding="utf-8") as file:
        cloud_state = json.load(file)

    graph = build_cloud_graph(cloud_state)

    for subnet in cloud_state["subnets"]:
        assert graph.has_edge(
            subnet["vpc_id"],
            subnet["id"]
        )

    for instance in cloud_state["instances"]:
        assert graph.has_edge(
            instance["subnet_id"],
            instance["id"]
        )

        for security_group_id in instance["security_group_ids"]:
            assert graph.has_edge(
                security_group_id,
                instance["id"]
            )


def test_public_security_group_ingress_reaches_graph():
    mock_file = Path("data/mock_aws_state.json")

    with mock_file.open("r", encoding="utf-8") as file:
        cloud_state = json.load(file)

    graph = build_cloud_graph(cloud_state)

    for security_group in cloud_state["security_groups"]:
        for rule in security_group.get("ingress_rules", []):
            if rule.get("source") == "0.0.0.0/0":
                assert graph.has_edge(
                    "internet",
                    security_group["id"]
                )        



def test_collect_aws_state_handles_empty_aws_response():
    class EmptyEC2Client:
        def describe_vpcs(self):
            return {"Vpcs": []}

        def describe_instances(self):
            return {"Reservations": []}

    client = EmptyEC2Client()

    state = collect_aws_state(ec2_client=client)

    assert state["vpcs"] == []
    assert state["instances"] == []                



def test_collect_aws_state_handles_missing_aws_lists():
    class MissingResourceEC2Client:
        def describe_vpcs(self):
            return {}

        def describe_instances(self):
            return {}

    client = MissingResourceEC2Client()

    state = collect_aws_state(ec2_client=client)

    assert state["vpcs"] == []
    assert state["instances"] == []    



def test_collect_aws_state_falls_back_when_aws_client_fails():
    class FailingEC2Client:
        def describe_vpcs(self):
            raise RuntimeError("AWS unavailable")

        def describe_instances(self):
            raise RuntimeError("AWS unavailable")

    client = FailingEC2Client()

    state = collect_aws_state(ec2_client=client)

    assert "vpcs" in state
    assert "instances" in state
    assert len(state["vpcs"]) > 0
    assert len(state["instances"]) > 0    