from app.remediation.workflow import remediate_finding


class FakeEC2:
    def __init__(self):
        self.revoked_rules = []

    def revoke_security_group_ingress(self, **kwargs):
        self.revoked_rules.append(kwargs)


class FakeBoto3:
    def __init__(self):
        self.ec2 = FakeEC2()

    def client(self, service_name):
        assert service_name == "ec2"
        return self.ec2


def test_remediation_workflow_revokes_public_ingress():
    finding = {
        "severity": "CRITICAL",
        "resource_id": "i-002",
        "resource_name": "db-server-1",
        "security_groups": ["sg-002"],
        "reason": "Public internet path detected to database",
        "path": ["internet", "sg-002", "i-002"],
    }

    fake_boto3 = FakeBoto3()

    code = remediate_finding(
        finding,
        boto3_module=fake_boto3,
    )

    assert "revoke_security_group_ingress" in code

    assert len(fake_boto3.ec2.revoked_rules) == 1

    rule = fake_boto3.ec2.revoked_rules[0]

    assert rule["GroupId"] == "sg-002"
    assert rule["IpPermissions"][0]["IpProtocol"] == "tcp"
    assert rule["IpPermissions"][0]["FromPort"] == 22
    assert rule["IpPermissions"][0]["ToPort"] == 22
    assert rule["IpPermissions"][0]["IpRanges"][0]["CidrIp"] == "0.0.0.0/0"


def test_remediation_workflow_rejects_missing_security_group():
    finding = {
        "severity": "CRITICAL",
        "resource_id": "i-002",
        "resource_name": "db-server-1",
        "security_groups": [],
        "path": ["internet", "i-002"],
    }

    fake_boto3 = FakeBoto3()

    try:
        remediate_finding(
            finding,
            boto3_module=fake_boto3,
        )
    except ValueError as error:
        assert "security group" in str(error).lower()
    else:
        raise AssertionError(
            "Expected ValueError for missing security group"
        )
    