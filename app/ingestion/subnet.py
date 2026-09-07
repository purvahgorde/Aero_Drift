def collect_subnets(ec2_client):
    """Collect subnet information from AWS."""
    response = ec2_client.describe_subnets()

    subnets = []

    for subnet in response.get("Subnets", []):
        subnets.append({
            "id": subnet["SubnetId"],
            "vpc_id": subnet.get("VpcId"),
            "cidr": subnet.get("CidrBlock"),
            "availability_zone": subnet.get("AvailabilityZone")
        })

    return subnets