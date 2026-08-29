from app.remediation.generator import generate_revoke_ingress_code
from app.remediation.sandbox import execute_remediation


def remediate_finding(finding, boto3_module):
    """
    Generate and execute remediation for a detected security finding.

    Currently supports public security group ingress findings.
    """

    security_groups = finding.get("security_groups", [])

    if not security_groups:
        raise ValueError("Finding does not contain a security group")

    path = finding.get("path", [])

    if len(path) < 2:
        raise ValueError("Finding does not contain a valid network path")

    security_group_id = security_groups[0]

    # For the current AeroDrift model, the public ingress
    # rule is TCP port 22 from the Internet.
    code = generate_revoke_ingress_code(
        security_group_id=security_group_id,
        protocol="tcp",
        from_port=22,
        to_port=22,
        source="0.0.0.0/0",
    )

    execute_remediation(
        code,
        boto3_module=boto3_module,
    )

    return code