import pytest

from app.remediation.generator import generate_revoke_ingress_code
from app.remediation.validator import (
    UnsafeRemediationError,
    validate_remediation_code,
)
from app.remediation.sandbox import execute_remediation


def test_generator_creates_revoke_ingress_code():
    code = generate_revoke_ingress_code(
        "sg-002",
        "tcp",
        22,
        22,
        "0.0.0.0/0",
    )

    assert "revoke_security_group_ingress" in code
    assert "sg-002" in code
    assert "tcp" in code
    assert "22" in code
    assert "0.0.0.0/0" in code


def test_validator_accepts_generated_code():
    code = generate_revoke_ingress_code(
        "sg-002",
        "tcp",
        22,
        22,
        "0.0.0.0/0",
    )

    assert validate_remediation_code(code) is True


def test_validator_rejects_unsafe_import():
    code = "import os"

    with pytest.raises(UnsafeRemediationError):
        validate_remediation_code(code)


def test_validator_rejects_unsafe_function_call():
    code = """
import boto3

boto3.client("ec2")
open("secret.txt", "w")
"""

    with pytest.raises(UnsafeRemediationError):
        validate_remediation_code(code)


class FakeEC2Client:
    def __init__(self):
        self.called = False
        self.kwargs = None

    def revoke_security_group_ingress(self, **kwargs):
        self.called = True
        self.kwargs = kwargs


class FakeBoto3:
    def __init__(self):
        self.ec2_client = FakeEC2Client()

    def client(self, service_name):
        assert service_name == "ec2"
        return self.ec2_client


def test_sandbox_executes_valid_remediation():
    code = generate_revoke_ingress_code(
        "sg-002",
        "tcp",
        22,
        22,
        "0.0.0.0/0",
    )

    fake_boto3 = FakeBoto3()

    execute_remediation(
        code,
        boto3_module=fake_boto3,
    )

    assert fake_boto3.ec2_client.called is True

    assert fake_boto3.ec2_client.kwargs["GroupId"] == "sg-002"

    assert fake_boto3.ec2_client.kwargs["IpPermissions"][0]["IpProtocol"] == "tcp"

    assert fake_boto3.ec2_client.kwargs["IpPermissions"][0]["FromPort"] == 22

    assert fake_boto3.ec2_client.kwargs["IpPermissions"][0]["ToPort"] == 22

    assert (
        fake_boto3.ec2_client.kwargs["IpPermissions"][0]["IpRanges"][0]["CidrIp"]
        == "0.0.0.0/0"
    )


def test_sandbox_rejects_unsafe_code():
    code = "import os"

    with pytest.raises(UnsafeRemediationError):
        execute_remediation(code)