# Aero_Drift

AeroDrift is a Python-based CloudOps engine that monitors AWS infrastructure for configuration drift and security anomalies. It uses NetworkX, boto3, asyncio, AST, SQLite, and Rich CLI to detect risks, automate remediation, and track cloud-state changes.

## Project Overview

AeroDrift collects AWS infrastructure state, builds a cloud topology graph, identifies security risks and configuration drift, and generates controlled remediation suggestions.

## AWS Ingestion

The AWS ingestion module collects core AWS infrastructure information for the AeroDrift cloud audit pipeline.

### Resource Collection

The cloud state includes:

- VPCs
- Subnets
- EC2 instances
- Security Groups
- EC2 instance relationships
- Security Group ingress relationships

The stable demonstration infrastructure is maintained in:

`data/mock_aws_state.json`

### Ingestion Flow

```text
AWS / Mock Infrastructure
          |
          v
AWS Ingestion Collector
          |
          v
Cloud State
          |
          v
NetworkX Cloud Topology
          |
          v
Security & Drift Detection
          |
          v
Remediation Workflow