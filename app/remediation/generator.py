def generate_revoke_ingress_code(
    security_group_id: str,
    protocol: str,
    from_port: int,
    to_port: int,
    source: str,
) -> str:
    """Generate boto3 code to revoke a security group ingress rule."""

    return f'''import boto3

ec2 = boto3.client("ec2")

ec2.revoke_security_group_ingress(
    GroupId={security_group_id!r},
    IpPermissions=[
        {{
            "IpProtocol": {protocol!r},
            "FromPort": {from_port},
            "ToPort": {to_port},
            "IpRanges": [
                {{"CidrIp": {source!r}}}
            ],
        }}
    ],
)
'''
