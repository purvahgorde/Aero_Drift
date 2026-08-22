from app.detection.security_analysis import allows_public_ingress


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


print("Day 7 test passed!")