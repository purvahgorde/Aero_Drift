def allows_public_ingress(security_group):
    """
    Check whether a security group allows inbound traffic
    from the entire IPv4 Internet (0.0.0.0/0).
    """

    ingress_rules = security_group.get("ingress_rules", [])

    for rule in ingress_rules:
        for ip_range in rule.get("IpRanges", []):
            if ip_range.get("CidrIp") == "0.0.0.0/0":
                return True

    return False