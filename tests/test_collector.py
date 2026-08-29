import json
from pathlib import Path

from app.ingestion.collector import collect_aws_state


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