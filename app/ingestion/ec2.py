def collect_ec2_instances(ec2_client):
    """Collect EC2 instance information from AWS."""
    response = ec2_client.describe_instances()

    instances = []

    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            security_group_ids = [
                security_group["GroupId"]
                for security_group in instance.get("SecurityGroups", [])
            ]

            instances.append({
                "id": instance["InstanceId"],
                "subnet_id": instance.get("SubnetId"),
                "vpc_id": instance.get("VpcId"),
                "state": instance.get("State", {}).get("Name"),
                "security_group_ids": security_group_ids
            })

    return instances