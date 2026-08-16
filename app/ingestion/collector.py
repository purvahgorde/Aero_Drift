from app.ingestion.aws_client import get_ec2_client
from app.ingestion.vpc import collect_vpcs
from app.ingestion.ec2 import collect_ec2_instances


def collect_aws_state(ec2_client=None):
    """Collect VPC and EC2 information into one AWS state object."""

    if ec2_client is None:
        ec2_client = get_ec2_client()

    return {
        "vpcs": collect_vpcs(ec2_client),
        "instances": collect_ec2_instances(ec2_client)
    }