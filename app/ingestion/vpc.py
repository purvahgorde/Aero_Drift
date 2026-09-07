def collect_vpcs(ec2_client):
    """Collect VPC information from AWS."""
    response = ec2_client.describe_vpcs()

    vpcs = []

    for vpc in response.get("Vpcs", []):
        vpcs.append({
            "id": vpc["VpcId"],
            "cidr": vpc.get("CidrBlock"),
            "state": vpc.get("State"),
            "tags": vpc.get("Tags", [])
        })

    return vpcs