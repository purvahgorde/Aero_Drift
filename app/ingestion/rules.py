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


def is_public_ipv4_rule(rule):
    """Return True if a parsed rule allows traffic from the entire IPv4 internet."""

    return rule.get("source") == "0.0.0.0/0"


def is_public_ipv6_rule(rule):
    """Return True if a parsed rule allows traffic from the entire IPv6 internet."""

    return rule.get("source") == "::/0"


def is_public_rule(rule):
    """Return True if a parsed rule allows traffic from the public internet."""

    return is_public_ipv4_rule(rule) or is_public_ipv6_rule(rule)


def is_all_traffic_rule(rule):
    """Return True if a rule allows all protocols."""

    return rule.get("protocol") == "-1"


def is_security_group_rule(rule):
    """Return True if a rule uses another security group as its source."""

    source = rule.get("source")

    return isinstance(source, str) and source.startswith("sg-")


def is_port_exposed(rule, port):
    """Return True if a rule allows traffic to the specified port."""

    if is_all_traffic_rule(rule):
        return True

    from_port = rule.get("from_port")
    to_port = rule.get("to_port")

    if from_port is None or to_port is None:
        return False

    return from_port <= port <= to_port