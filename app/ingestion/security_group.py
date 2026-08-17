def collect_security_groups(ec2_client):
    """Collect security group information from AWS."""
    response = ec2_client.describe_security_groups()

    security_groups = []

    for security_group in response.get("SecurityGroups", []):
        security_groups.append({
            "id": security_group["GroupId"],
            "vpc_id": security_group.get("VpcId"),
            "name": security_group.get("GroupName"),
            "description": security_group.get("Description"),
            "ingress_rules": security_group.get("IpPermissions", []),
            "egress_rules": security_group.get("IpPermissionsEgress", [])
        })

    return security_groups