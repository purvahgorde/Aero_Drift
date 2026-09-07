AeroDrift
CloudOps & Security Configuration Drift Detection Platform

AeroDrift is a Python-based CloudOps and security-analysis system that monitors cloud infrastructure, detects configuration changes, identifies security risks, and provides remediation suggestions.

Key Features
Cloud Resource Ingestion: Collects VPC, Subnet, EC2, Security Group, and Database information from AWS or mock data.
Cloud Topology: Uses NetworkX to represent cloud resources and their relationships as a directed graph.
Security Analysis: Detects publicly exposed Security Groups and EC2 instances and checks their paths to databases.
Drift Detection: Identifies added, removed, or changed resources and relationships.
Remediation: Generates suggestions to review and fix detected configuration changes.
CLI & Dashboard: Provides infrastructure summaries, topology views, and security information.
Technologies Used

Python | Boto3 | NetworkX | Rich | SQLite | JSON

Project Workflow

AWS / Mock Data
      ↓
Resource Ingestion
      ↓
NetworkX Cloud Topology
      ↓
Security Analysis + Drift Detection
      ↓
Remediation Suggestions
      ↓
CLI / Dashboard

Installation & Run
pip install -r requirements.txt
python -m app.main

CLI Commands
python -m app.main summary
python -m app.main topology
python -m app.main dashboard
python -m app.main config

Team Responsibilities
Member 1: AWS/Mock Resource Ingestion
Member 2: Security Analysis
Member 3: NetworkX Topology, Drift Detection & Remediation
Member 4: CLI, Dashboard & System Integration
