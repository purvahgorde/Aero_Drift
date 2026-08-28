from app.ingestion.rules import parse_ingress_rules


def collect_security_groups(ec2_client):
    """Collect security group information from AWS.

    Raw AWS ingress rules are preserved in ``ingress_rules`` while
    ``parsed_ingress_rules`` contains the normalized representation
    produced by the network security rule parser.
    """

    response = ec2_client.describe_security_groups()

    security_groups = []

    for security_group in response.get("SecurityGroups", []):
        raw_ingress_rules = security_group.get("IpPermissions", [])

        security_groups.append({
            "id": security_group["GroupId"],
            "vpc_id": security_group.get("VpcId"),
            "name": security_group.get("GroupName"),
            "description": security_group.get("Description"),

            # Preserve the original AWS representation.
            "ingress_rules": raw_ingress_rules,

            # Add the normalized representation for security analysis.
            "parsed_ingress_rules": parse_ingress_rules({
                "ingress_rules": raw_ingress_rules
            }),

            "egress_rules": security_group.get(
                "IpPermissionsEgress", []
            )
        })

    return security_groups