def parse_ingress_rules(security_group):
    """Parse AWS security group ingress rules into a simpler format."""

    rules = []

    for permission in security_group.get("ingress_rules", []):
        protocol = permission.get("IpProtocol")

        from_port = permission.get("FromPort")
        to_port = permission.get("ToPort")

        for ip_range in permission.get("IpRanges", []):
            rules.append({
                "protocol": protocol,
                "from_port": from_port,
                "to_port": to_port,
                "source": ip_range.get("CidrIp")
            })

    return rules
