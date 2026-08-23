import json
import os

from app.ingestion.aws_client import get_ec2_client
from app.ingestion.vpc import collect_vpcs
from app.ingestion.ec2 import collect_ec2_instances


def collect_aws_state(ec2_client=None):
    """Collect VPC and EC2 information into one AWS state object."""

    if ec2_client is None:
        try:
            ec2_client = get_ec2_client()

            return {
                "vpcs": collect_vpcs(ec2_client),
                "instances": collect_ec2_instances(ec2_client),
            }

        except Exception:
            # Fall back to mock data when AWS credentials are unavailable.
            mock_file = os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(__file__)
                    )
                ),
                "data",
                "mock_aws_state.json",
            )

            if os.path.exists(mock_file):
                with open(mock_file, "r") as f:
                    data = json.load(f)

                return {
                    "vpcs": data.get("vpcs", []),
                    "instances": data.get("instances", []),
                }

            return {
                "vpcs": [],
                "instances": [],
            }

    return {
        "vpcs": collect_vpcs(ec2_client),
        "instances": collect_ec2_instances(ec2_client),
    }


def collect_all_resources(ec2_client=None):
    """Alias for collect_aws_state."""
    return collect_aws_state(ec2_client=ec2_client)