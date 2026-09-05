# AWS Ingestion Documentation

## Purpose

The AWS ingestion module collects infrastructure information required by the AeroDrift cloud audit pipeline.

## Resources

The ingestion layer works with:

- VPCs
- EC2 instances
- Subnet relationships
- Security Group relationships
- Resource identifiers and states

## AWS Collection Flow

```text
AWS EC2 API
    |
    v
aws_client.py
    |
    v
collector.py
    |
    +--> vpc.py
    |
    +--> ec2.py
    |
    v
Cloud State