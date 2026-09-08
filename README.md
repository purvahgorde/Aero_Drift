<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/NetworkX-Graph_Engine-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/SQLite-Persistence-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/boto3-AWS_SDK-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white" />
  <img src="https://img.shields.io/badge/Tests-111_Passed-brightgreen?style=for-the-badge" />
</p>

<h1 align="center">🌬️ AeroDrift</h1>

<p align="center">
  <strong>Cloud Infrastructure Drift Detection, Security Analysis & Automated Remediation Platform</strong>
</p>

<p align="center">
  <em>A production-grade Python engine that monitors AWS infrastructure for configuration drift and security anomalies — powered by NetworkX, boto3, AST-based code generation, SQLite persistence, and a Rich CLI dashboard.</em>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [Dashboard Output](#-dashboard-output)
- [SQLite Persistence](#-sqlite-persistence)
- [Testing](#-testing)
- [Tech Stack](#-tech-stack)
- [Team Members](#-team-members)
- [License](#-license)

---

## 🔍 Overview

**AeroDrift** is a comprehensive CloudOps platform that provides end-to-end visibility into your AWS infrastructure. It automatically collects resource states, builds a topology graph, detects configuration drift and security vulnerabilities, and generates validated remediation code — all from a single CLI interface.

### Why AeroDrift?

| Problem | AeroDrift Solution |
|---|---|
| Infrastructure changes go unnoticed | **Drift Detection** compares topology snapshots to identify every change |
| Security misconfigurations are hard to find | **Graph-based Security Analysis** traces public internet paths to sensitive resources |
| Remediation is manual and error-prone | **AST-validated Code Generation** creates safe, auditable boto3 remediation scripts |
| No historical record of cloud state | **SQLite Persistence** stores every scan, finding, and remediation result |

---

## ✨ Key Features

### 🔄 Data Ingestion
- Automated collection of AWS resources (VPCs, Subnets, EC2, Security Groups)
- Mock data support for development and demos — no AWS credentials required
- Structured resource parsing with ingress rule analysis

### 🗺️ Topology Mapping
- Builds a **NetworkX directed graph** of all infrastructure relationships
- Maps VPC → Subnet → EC2 Instance → Security Group hierarchies
- Supports path finding, neighbor discovery, and subgraph extraction

### 🛡️ Security Analysis
- **Public Database Exposure Detection** — finds internet-reachable database instances
- **Ingress Rule Analysis** — identifies overly permissive security group rules (e.g., `0.0.0.0/0` on port 22)
- Graph-traversal-based vulnerability detection with severity classification

### 📊 Configuration Drift Detection
- Compares two topology snapshots to detect:
  - **Added** nodes and edges (new resources)
  - **Removed** nodes and edges (deleted resources)
  - **Changed** node attributes (modified configurations)
- Field-level change tracking with previous/current value comparison

### 🔧 Automated Remediation
- **Code Generator** — produces boto3 remediation scripts (e.g., `revoke_security_group_ingress`)
- **AST Validator** — statically analyzes generated code to ensure only safe operations are used
- **Sandboxed Execution** — runs validated code in a restricted environment with no builtins
- **Workflow Engine** — end-to-end finding → code generation → validation → execution pipeline

### 💾 SQLite Persistence
- Stores scan history, resource states, security findings, and remediation results
- WAL mode for concurrent read performance
- Foreign key constraints for referential integrity
- Full CRUD operations with context manager support

### 🖥️ Rich CLI Dashboard
- Professional terminal dashboard with panels, tables, and tree views
- System overview with resource counts, finding severity, and status indicators
- Interactive topology tree visualization
- Side-by-side infrastructure and security summary panels

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AeroDrift Pipeline                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│   │  INGESTION   │───▶│   TOPOLOGY   │───▶│  DRIFT DETECTION     │  │
│   │              │    │    GRAPH     │    │  & SECURITY ANALYSIS │  │
│   │ • VPCs       │    │              │    │                      │  │
│   │ • Subnets    │    │  NetworkX    │    │ • Node/Edge changes  │  │
│   │ • EC2        │    │  DiGraph     │    │ • Public DB exposure │  │
│   │ • Sec Groups │    │              │    │ • Ingress analysis   │  │
│   └──────────────┘    └──────────────┘    └──────────┬───────────┘  │
│                                                      │              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────▼───────────┐  │
│   │   SQLITE     │◀───│  DASHBOARD   │◀───│    REMEDIATION       │  │
│   │ PERSISTENCE  │    │   (Rich)     │    │                      │  │
│   │              │    │              │    │ • Code generation    │  │
│   │ • Scans      │    │ • Overview   │    │ • AST validation     │  │
│   │ • Resources  │    │ • Topology   │    │ • Sandbox execution  │  │
│   │ • Findings   │    │ • Findings   │    │ • Workflow engine    │  │
│   │ • Remediation│    │ • Actions    │    │                      │  │
│   └──────────────┘    └──────────────┘    └──────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Aero_Drift/
│
├── app/
│   ├── main.py                    # CLI entry point with command dispatch
│   ├── config.py                  # YAML configuration with validation & defaults
│   │
│   ├── ingestion/                 # AWS Resource Collection
│   │   ├── collector.py           # Main collection orchestrator
│   │   ├── aws_client.py          # boto3 client factory
│   │   ├── ec2.py                 # EC2 instance collector
│   │   ├── vpc.py                 # VPC collector
│   │   ├── subnet.py              # Subnet collector
│   │   ├── security_group.py      # Security group collector
│   │   └── rules.py               # Ingress rule parser & analyzer
│   │
│   ├── graph/                     # Topology Graph Engine
│   │   ├── topology.py            # CloudTopology (NetworkX DiGraph)
│   │   ├── builder.py             # Graph builder with internet gateway node
│   │   ├── drift_detector.py      # Public database exposure detector
│   │   └── nodes.py               # CloudNode data class
│   │
│   ├── detection/                 # Security & Drift Analysis
│   │   ├── security_analysis.py   # Public ingress & DB path detection
│   │   └── drift_detector.py      # Topology snapshot comparison
│   │
│   ├── persistence/               # SQLite Data Layer
│   │   ├── database.py            # AeroDriftDB — full CRUD manager
│   │   └── models.py              # Scan comparison & drift summaries
│   │
│   ├── remediation/               # Automated Remediation
│   │   ├── generator.py           # boto3 remediation code generator
│   │   ├── validator.py           # AST-based safety validator
│   │   ├── sandbox.py             # Restricted execution environment
│   │   └── workflow.py            # End-to-end remediation workflow
│   │
│   └── dashboard/                 # Rich CLI Dashboard
│       ├── cli.py                 # Full dashboard renderer with panels
│       ├── cli_dashboard.py       # Dashboard wrapper class
│       ├── audit.py               # Security drift findings table
│       ├── summary.py             # Resource summary display
│       └── topology_view.py       # Tree-view topology renderer
│
├── tests/                         # 111 pytest tests (100% pass rate)
│   ├── test_cli.py                # CLI command dispatch tests
│   ├── test_collector.py          # Data ingestion tests
│   ├── test_config.py             # Configuration loading tests
│   ├── test_dashboard.py          # Dashboard rendering tests
│   ├── test_drift_detector.py     # Drift detection tests
│   ├── test_graph.py              # Graph builder & security tests
│   ├── test_ingestion.py          # Ingress rule parsing tests
│   ├── test_integration.py        # End-to-end integration tests
│   ├── test_network_graph.py      # Network graph construction tests
│   ├── test_remediation.py        # Code gen, validation & sandbox tests
│   ├── test_remediation_workflow.py # Workflow integration tests
│   ├── test_security_analysis.py  # Security analysis tests
│   ├── test_smoke.py              # Basic import smoke test
│   └── test_topology.py           # Topology graph operation tests
│
├── data/
│   └── mock_aws_state.json        # Mock AWS infrastructure data
│
├── config.yaml                    # Central YAML configuration
├── requirements.txt               # Python dependencies
├── demo.py                        # Full feature demonstration script
└── README.md
```

---

## 🚀 Installation

### Prerequisites
- Python 3.10+ (developed with Python 3.13)
- pip package manager

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/purvahgorde/Aero_Drift.git
cd Aero_Drift

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 💻 Usage

AeroDrift provides a comprehensive CLI with multiple commands:

```bash
# Run the full demo (recommended first run)
python demo.py

# Run the full pipeline (collect → build → display)
python -m app.main

# Individual commands
python -m app.main summary      # Infrastructure summary
python -m app.main topology     # Topology graph tree view
python -m app.main dashboard    # Full interactive security dashboard
python -m app.main security     # Security findings report
python -m app.main drift        # Configuration drift detection
python -m app.main config       # Display current configuration
python -m app.main scan         # Quick scan (non-interactive)
python -m app.main --help       # Show all available commands
```

---

## 📸 Dashboard Output

### Full Security Dashboard

The interactive dashboard provides a unified view of infrastructure, security, and remediation status:

```
╭───────────────────────────────────────────────────────────────────╮
│                            AERODRIFT                              │
│              CloudOps Security & Topology Analyzer                │
╰───────────────────────────────────────────────────────────────────╯
╭─ SYSTEM OVERVIEW ─────────────────────────────────────────────────╮
│ Resources │ Nodes │ Connections │ Findings │ High Risk │  Status  │
│     7     │   7   │      6      │    1     │     1     │! CRITICAL│
╰───────────────────────────────────────────────────────────────────╯
╭─ INFRASTRUCTURE ──────────╮  ╭─ SECURITY SUMMARY ────────────────╮
│ VPCs                    1 │  │ HIGH                            1  │
│ Subnets                 2 │  │ MEDIUM                          0  │
│ EC2 Instances           2 │  │ LOW                             0  │
│ Security Groups         2 │  │ SECURE                          6  │
╰───────────────────────────╯  ╰────────────────────────────────────╯
╭─ CLOUD TOPOLOGY ──────────────────────────────────────────────────╮
│ └── VPC: vpc-001 (AeroDrift-VPC)                                  │
│     ├── Subnet: subnet-001                                        │
│     │   └── EC2: i-001 (web-server-1)                             │
│     │       └── SecurityGroup: sg-001 (web-sg)                    │
│     └── Subnet: subnet-002                                        │
│         └── EC2: i-002 (db-server-1)                              │
│             └── SecurityGroup: sg-002 (db-sg)                     │
╰───────────────────────────────────────────────────────────────────╯
╭─ SECURITY FINDINGS ──────────────────────────────────────────────╮
│ [CRITICAL] i-002                                                  │
│   Public internet path detected to database                       │
╰───────────────────────────────────────────────────────────────────╯
╭─ REMEDIATION ─────────────────────────────────────────────────────╮
│ (!) 1 remediation action(s) recommended                           │
│                                                                   │
│   1. Remove public network path to database. Restrict security    │
│      group rules on sg-002.                                       │
╰───────────────────────────────────────────────────────────────────╯
╭─ QUICK ACTIONS ───────────────────────────────────────────────────╮
│ [1] Scan Infrastructure  [2] View Findings  [3] View Topology     │
│ [4] Remediation  [Q] Exit                                         │
╰───────────────────────────────────────────────────────────────────╯
```

### Infrastructure Summary

```
      AeroDrift Infrastructure Summary
┌─────────────────┬───────┐
│ Resource        │ Count │
├─────────────────┼───────┤
│ VPCs            │     1 │
│ Subnets         │     2 │
│ EC2 Instances   │     2 │
│ Security Groups │     2 │
└─────────────────┴───────┘
```

### Topology Tree View

```
AeroDrift Cloud Topology
└── VPC: vpc-001 (AeroDrift-VPC)
    ├── Subnet: subnet-001
    │   └── EC2: i-001 (web-server-1)
    │       └── SecurityGroup: sg-001 (web-sg)
    └── Subnet: subnet-002
        └── EC2: i-002 (db-server-1)
            └── SecurityGroup: sg-002 (db-sg)
```

### Security Findings

```
                       AeroDrift Security Drift
┌──────────┬────────────────────┬──────────┬─────────────────────────────────────────┬──────────────────────────┐
│ Severity │ Resource           │ Security │ Reason                                  │ Network Path             │
│          │                    │ Group    │                                         │                          │
├──────────┼────────────────────┼──────────┼─────────────────────────────────────────┼──────────────────────────┤
│ CRITICAL │ db-server-1 (i-002)│ sg-002   │ Public internet path detected to        │ internet → sg-002 → i-002│
│          │                    │          │ database                                │                          │
└──────────┴────────────────────┴──────────┴─────────────────────────────────────────┴──────────────────────────┘
```

### Drift Detection Results

```
========================================
     DRIFT DETECTION RESULTS
========================================

  Nodes added    : 2
    + subnet-002
    + sg-002
  Nodes removed  : 0
  Nodes changed  : 1
    ~ i-001
        state: running → stopped
        name: web-server-1 → production-server

  Edges added    : 1
    + vpc-001 → subnet-002
  Edges removed  : 0

  Status: DRIFT DETECTED (4 change(s))
========================================
```

### Configuration Display

```
========================================
     AERODRIFT CONFIGURATION
========================================

  App Name           : AeroDrift
  Description        : Cloud Topology & Remediation Platform
  Version            : 0.1.0

  AWS Region         : us-east-1
  Mock Data Path     : data/mock_aws_state.json

  Log Level          : INFO
  Verbose            : False

========================================
```

---

## 💾 SQLite Persistence

AeroDrift uses SQLite for lightweight, zero-configuration data persistence. All scan data is stored locally with full CRUD operations.

### Database Schema

| Table | Purpose | Key Columns |
|---|---|---|
| `scan_history` | Tracks every scan execution | `scan_id`, `timestamp`, `status` |
| `resources` | Stores resource state snapshots | `scan_id`, `resource_id`, `resource_type`, `resource_state` |
| `security_findings` | Records detected vulnerabilities | `scan_id`, `resource_id`, `severity`, `title`, `description` |
| `remediation_results` | Logs remediation actions | `scan_id`, `resource_id`, `action`, `status` |

### Usage Example

```python
from app.persistence.database import AeroDriftDB

# Initialize database (auto-creates tables)
with AeroDriftDB() as db:
    # Create a scan record
    scan_id = db.create_scan("completed")

    # Save collected resources
    db.save_resources(scan_id, resources)

    # Save security findings
    db.save_findings(scan_id, findings)

    # Save remediation results
    db.save_remediation_results(scan_id, results)

    # Query history
    latest_scan = db.get_latest_scan()
    all_scans = db.get_all_scans()
    scan_resources = db.get_resources_for_scan(scan_id)
```

### SQLite Integration Verification

```
==================================================
   AERODRIFT SQLITE INTEGRATION TEST
==================================================

  [PASS] 1. Created scan: ef9a7e9e...
  [PASS] 2. Resources saved successfully
  [PASS] 3. Findings saved successfully
  [PASS] 4. Latest scan retrieved: status=completed
  [PASS] 5. Resources retrieved: 4 rows
  [PASS] 6. Findings retrieved: 1 rows
  [PASS] 7. Remediation results: 1 rows
  [PASS] 8. Previous scan retrieval works
  [PASS] 9. Total scans: 2
  [PASS] 10. Context manager works

==================================================
   ALL SQLITE INTEGRATION TESTS PASSED!
==================================================
```

---

## 🧪 Testing

AeroDrift has a comprehensive test suite with **111 tests** covering all modules:

```bash
# Run the full test suite
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --tb=short
```

### Test Results

```
========================= test session starts =========================
platform win32 -- Python 3.13.15, pytest-9.1.1
collected 111 items

tests/test_cli.py              ✅ 17 passed    (CLI command dispatch)
tests/test_collector.py        ✅  3 passed    (Data ingestion)
tests/test_config.py           ✅ 20 passed    (Configuration loading)
tests/test_dashboard.py        ✅  1 passed    (Dashboard rendering)
tests/test_drift_detector.py   ✅  1 passed    (Drift detection)
tests/test_graph.py            ✅  7 passed    (Graph builder & security)
tests/test_ingestion.py        ✅ 16 passed    (Ingress rule parsing)
tests/test_integration.py      ✅ 25 passed    (End-to-end integration)
tests/test_network_graph.py    ✅  1 passed    (Network graph)
tests/test_remediation.py      ✅  6 passed    (Code gen & validation)
tests/test_remediation_workflow ✅  2 passed    (Workflow integration)
tests/test_security_analysis.py ✅ (included in integration)
tests/test_smoke.py            ✅  1 passed    (Import smoke test)
tests/test_topology.py         ✅ 13 passed    (Topology operations)

==================== 111 passed in 12.81s =============================
```

### Test Coverage by Module

| Module | Tests | Coverage |
|---|:---:|---|
| CLI (`app.main`) | 17 | Command dispatch, error handling, output validation |
| Config (`app.config`) | 20 | Loading, validation, defaults, env overrides, edge cases |
| Ingestion (`app.ingestion`) | 19 | VPC/EC2/Subnet/SG collection, ingress rule parsing |
| Graph (`app.graph`) | 21 | Topology building, path finding, drift detection |
| Detection (`app.detection`) | 1 | Topology drift comparison |
| Remediation (`app.remediation`) | 8 | Code generation, AST validation, sandbox execution |
| Dashboard (`app.dashboard`) | 1 | Rendering without crashes |
| Integration | 25 | Full pipeline end-to-end flows |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.13** | Core runtime |
| **NetworkX** | Graph data structure for topology mapping |
| **boto3** | AWS SDK for resource collection |
| **SQLite** | Lightweight embedded database for persistence |
| **Rich** | Terminal UI framework for dashboard rendering |
| **PyYAML** | Configuration file parsing |
| **AST (stdlib)** | Static analysis for remediation code validation |
| **pytest** | Testing framework |
| **Matplotlib** | Optional visualization support |

---

## 👥 Team Members

| Member | Responsibilities |
|--------|------------------|
| **Shivanandini Saddanapu** | AWS/Mock Resource Ingestion |
| **Purva Gorde** | NetworkX Topology, Drift Detection & Remediation |
| **Pranay Mahajan** | Security Analysis, CLI, Dashboard & System Integration |

---

## 📄 License

All rights reserved.

---

<p align="center">
  <strong>Built with ❤️ by the AeroDrift Team</strong>
</p>
