import boto3


def get_ec2_client():
    """Create and return an AWS EC2 client."""
    return boto3.client("ec2")