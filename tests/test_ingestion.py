import unittest

from app.ingestion.vpc import collect_vpcs
from app.ingestion.ec2 import collect_ec2_instances
from app.ingestion.subnet import collect_subnets
from app.ingestion.security_group import collect_security_groups
from app.ingestion.rules import parse_ingress_rules


class MockEC2Client:
    def describe_vpcs(self):
        return {
            "Vpcs": [
                {
                    "VpcId": "vpc-001",
                    "CidrBlock": "10.0.0.0/16",
                    "State": "available",
                    "Tags": [
                        {"Key": "Name", "Value": "test-vpc"}
                    ]
                }
            ]
        }

    def describe_instances(self):
        return {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-001",
                            "SubnetId": "subnet-001",
                            "VpcId": "vpc-001",
                            "State": {"Name": "running"},
                            "SecurityGroups": [
                                {"GroupId": "sg-001"}
                            ]
                        }
                    ]
                }
            ]
        }

    def describe_subnets(self):
        return {
            "Subnets": [
                {
                    "SubnetId": "subnet-001",
                    "VpcId": "vpc-001",
                    "CidrBlock": "10.0.1.0/24",
                    "AvailabilityZone": "ap-south-1a"
                }
            ]
        }

    def describe_security_groups(self):
        return {
            "SecurityGroups": [
                {
                    "GroupId": "sg-001",
                    "VpcId": "vpc-001",
                    "GroupName": "web-server",
                    "Description": "Web server security group",
                    "IpPermissions": [
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 80,
                            "ToPort": 80,
                            "IpRanges": [
                                {"CidrIp": "0.0.0.0/0"}
                            ]
                        }
                    ],
                    "IpPermissionsEgress": [
                        {
                            "IpProtocol": "-1",
                            "IpRanges": [
                                {"CidrIp": "0.0.0.0/0"}
                            ]
                        }
                    ]
                }
            ]
        }


class TestIngestion(unittest.TestCase):

    def test_collect_vpcs(self):
        result = collect_vpcs(MockEC2Client())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "vpc-001")
        self.assertEqual(result[0]["cidr"], "10.0.0.0/16")
        self.assertEqual(result[0]["state"], "available")
        self.assertEqual(result[0]["tags"][0]["Key"], "Name")

    def test_collect_ec2_instances(self):
        result = collect_ec2_instances(MockEC2Client())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "i-001")
        self.assertEqual(result[0]["subnet_id"], "subnet-001")
        self.assertEqual(result[0]["vpc_id"], "vpc-001")
        self.assertEqual(result[0]["state"], "running")
        self.assertEqual(result[0]["security_group_ids"], ["sg-001"])

    def test_collect_subnets(self):
        result = collect_subnets(MockEC2Client())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "subnet-001")
        self.assertEqual(result[0]["vpc_id"], "vpc-001")
        self.assertEqual(result[0]["cidr"], "10.0.1.0/24")

    def test_collect_security_groups(self):
        result = collect_security_groups(MockEC2Client())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "sg-001")
        self.assertEqual(result[0]["vpc_id"], "vpc-001")
        self.assertEqual(result[0]["name"], "web-server")
        self.assertEqual(len(result[0]["ingress_rules"]), 1)
        self.assertEqual(len(result[0]["egress_rules"]), 1)

    def test_parse_ingress_rules(self):
        security_group = {
            "ingress_rules": [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [
                        {"CidrIp": "10.0.0.0/8"},
                        {"CidrIp": "192.168.1.0/24"}
                    ]
                }
            ]
        }

        result = parse_ingress_rules(security_group)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["protocol"], "tcp")
        self.assertEqual(result[0]["from_port"], 22)
        self.assertEqual(result[0]["to_port"], 22)
        self.assertEqual(result[0]["source"], "10.0.0.0/8")
        self.assertEqual(result[1]["source"], "192.168.1.0/24")


if __name__ == "__main__":
    unittest.main()