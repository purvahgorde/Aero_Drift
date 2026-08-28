def parse_ingress_rules(security_group):
    """Parse AWS security group ingress rules into a simpler format."""

    rules = []

    for permission in security_group.get("ingress_rules", []):
        protocol = permission.get("IpProtocol")

        from_port = permission.get("FromPort")
        to_port = permission.get("ToPort")

        # IPv4 CIDR sources
        for ip_range in permission.get("IpRanges", []):
            rules.append({
                "protocol": protocol,
                "from_port": from_port,
                "to_port": to_port,
                "source": ip_range.get("CidrIp")
            })

        # IPv6 CIDR sources
        for ip_range in permission.get("Ipv6Ranges", []):
            rules.append({
                "protocol": protocol,
                "from_port": from_port,
                "to_port": to_port,
                "source": ip_range.get("CidrIpv6")
            })

        # Security group sources
        for group in permission.get("UserIdGroupPairs", []):
            rules.append({
                "protocol": protocol,
                "from_port": from_port,
                "to_port": to_port,
                "source": group.get("GroupId")
            })

    return rules