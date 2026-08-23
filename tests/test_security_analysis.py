from app.detection.security_analysis import allows_public_ingress
from app.detection.security_analysis import get_publicly_exposed_instances
from app.graph.topology import create_network_graph


# Security group with public ingress
public_security_group = {
    "id": "sg-001",
    "name": "public-web-sg",
    "ingress_rules": [
        {
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [
                {
                    "CidrIp": "0.0.0.0/0"
                }
            ]
        }
    ]
}


# Security group without public ingress
private_security_group = {
    "id": "sg-002",
    "name": "private-db-sg",
    "ingress_rules": [
        {
            "IpProtocol": "tcp",
            "FromPort": 3306,
            "ToPort": 3306,
            "IpRanges": [
                {
                    "CidrIp": "10.0.0.0/16"
                }
            ]
        }
    ]
}


public_result = allows_public_ingress(public_security_group)
private_result = allows_public_ingress(private_security_group)


print("Public security group:", public_result)
print("Private security group:", private_result)


assert public_result is True
assert private_result is False


# print("Day 7 test passed!")

resources = {
    "vpcs": [
        {
            "id": "vpc-001",
            "tags": [
                {
                    "Key": "Name",
                    "Value": "main-vpc"
                }
            ]
        }
    ],

    "subnets": [
        {
            "id": "subnet-001",
            "vpc_id": "vpc-001"
        }
    ],

    "instances": [
        {
            "id": "i-12345",
            "subnet_id": "subnet-001",
            "vpc_id": "vpc-001",
            "security_group_ids": ["sg-001"]
        }
    ],

    "security_groups": [
        {
            "id": "sg-001",
            "vpc_id": "vpc-001",
            "name": "public-web-sg",
            "ingress_rules": [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [
                        {
                            "CidrIp": "0.0.0.0/0"
                        }
                    ]
                }
            ],
            "egress_rules": []
        }
    ]
}
topology = create_network_graph(resources)

exposed_instances = get_publicly_exposed_instances(
    topology,
    resources["security_groups"]
)

print("Publicly exposed EC2 instances:", exposed_instances)

assert exposed_instances == ["i-12345"]
# print("Day 8 test passed!")