"""AeroDrift — Final Presentation Demo Script.

Run with:
    python demo.py

This script exercises every major feature of the AeroDrift platform
in sequence, producing clean output suitable for a live demo or
screen-recording.
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.dashboard.cli import show_welcome, render_dashboard
from app.dashboard.summary import show_summary
from app.dashboard.topology_view import render_topology
from app.dashboard.audit import show_drift_findings
from app.ingestion.collector import collect_all_resources
from app.graph.topology import create_network_graph, CloudTopology
from app.graph.builder import build_cloud_graph
from app.graph.drift_detector import detect_public_database_exposure
from app.detection.security_analysis import detect_security_findings
from app.detection.drift_detector import detect_drift
from app.graph.nodes import CloudNode
from app.config import load_config


def section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def main():
    section("AERODRIFT — FINAL PRESENTATION DEMO")

    # ── 1. Welcome Banner ────────────────────────────────────────
    section("1. WELCOME BANNER")
    show_welcome()

    # ── 2. Collect Resources ─────────────────────────────────────
    section("2. DATA INGESTION (Mock AWS)")
    resources = collect_all_resources()
    print(f"  Collected {sum(len(v) for v in resources.values())} resources:")
    print(f"    VPCs             : {len(resources.get('vpcs', []))}")
    print(f"    Subnets          : {len(resources.get('subnets', []))}")
    print(f"    EC2 Instances    : {len(resources.get('instances', []))}")
    print(f"    Security Groups  : {len(resources.get('security_groups', []))}")

    # ── 3. Infrastructure Summary ────────────────────────────────
    section("3. INFRASTRUCTURE SUMMARY")
    show_summary(resources)

    # ── 4. Build Topology Graph ──────────────────────────────────
    section("4. TOPOLOGY GRAPH")
    topology = create_network_graph(resources)
    graph_info = topology.get_graph_summary()
    print(f"  Built topology: {graph_info['nodes']} nodes, {graph_info['edges']} edges\n")
    render_topology(topology)

    # ── 5. Security Analysis ─────────────────────────────────────
    section("5. SECURITY ANALYSIS")

    # Graph-based detection (public database exposure)
    cloud_graph = build_cloud_graph(resources)
    graph_findings = detect_public_database_exposure(cloud_graph)

    if graph_findings:
        print(f"  Found {len(graph_findings)} security finding(s):\n")
        for i, f in enumerate(graph_findings, 1):
            print(f"  [{i}] [{f['severity']}] {f.get('resource_name', f['resource_id'])}")
            print(f"      Reason : {f['reason']}")
            print(f"      Path   : {' -> '.join(str(p) for p in f['path'])}")
            sgs = f.get("security_groups", [])
            if sgs:
                print(f"      SGs    : {', '.join(sgs)}")
            print()
    else:
        print("  No security findings detected.")

    # Display findings table
    if graph_findings:
        show_drift_findings(graph_findings)

    # ── 6. Configuration Drift Detection ─────────────────────────
    section("6. CONFIGURATION DRIFT DETECTION")

    # Build two topology snapshots with differences
    previous = CloudTopology()
    previous.add_node(CloudNode("vpc-001", "VPC", "AeroDrift-VPC"))
    previous.add_node(CloudNode("subnet-001", "Subnet"))
    previous.add_node(CloudNode("i-001", "EC2", "web-server-1"))
    previous.add_node(CloudNode("sg-001", "SecurityGroup", "web-sg"))
    previous.add_relationship("vpc-001", "subnet-001")
    previous.add_relationship("subnet-001", "i-001")
    previous.add_relationship("i-001", "sg-001")
    previous.graph.nodes["i-001"]["state"] = "running"
    previous.graph.nodes["i-001"]["subnet_id"] = "subnet-001"

    current = CloudTopology()
    current.add_node(CloudNode("vpc-001", "VPC", "AeroDrift-VPC"))
    current.add_node(CloudNode("subnet-001", "Subnet"))
    current.add_node(CloudNode("subnet-002", "Subnet"))
    current.add_node(CloudNode("i-001", "EC2", "production-server"))
    current.add_node(CloudNode("sg-001", "SecurityGroup", "web-sg"))
    current.add_node(CloudNode("sg-002", "SecurityGroup", "db-sg"))
    current.add_relationship("vpc-001", "subnet-001")
    current.add_relationship("vpc-001", "subnet-002")
    current.add_relationship("subnet-001", "i-001")
    current.add_relationship("i-001", "sg-001")
    current.graph.nodes["i-001"]["state"] = "stopped"
    current.graph.nodes["i-001"]["subnet_id"] = "subnet-001"

    drift = detect_drift(previous, current)

    added = drift["nodes"]["added"]
    removed = drift["nodes"]["removed"]
    changed = drift["nodes"]["changed"]
    rel_added = drift["relationships"]["added"]
    rel_removed = drift["relationships"]["removed"]

    print(f"  Nodes added    : {len(added)}")
    for n in added:
        print(f"    + {n}")
    print(f"  Nodes removed  : {len(removed)}")
    for n in removed:
        print(f"    - {n}")
    print(f"  Nodes changed  : {len(changed)}")
    for c in changed:
        print(f"    ~ {c['resource_id']}")
        for attr, vals in c["changes"].items():
            print(f"        {attr}: {vals['previous']} -> {vals['current']}")
    print()
    print(f"  Edges added    : {len(rel_added)}")
    for src, dst in rel_added:
        print(f"    + {src} -> {dst}")
    print(f"  Edges removed  : {len(rel_removed)}")
    for src, dst in rel_removed:
        print(f"    - {src} -> {dst}")

    total = len(added) + len(removed) + len(changed) + len(rel_added) + len(rel_removed)
    print(f"\n  Status: DRIFT DETECTED ({total} change(s))")

    # ── 7. Configuration Display ─────────────────────────────────
    section("7. CURRENT CONFIGURATION")
    config = load_config()
    print(f"  App Name           : {config.app.name}")
    print(f"  Description        : {config.app.description}")
    print(f"  Version            : {config.app.version}")
    print(f"  AWS Region         : {config.aws.region}")
    print(f"  Mock Data Path     : {config.aws.mock_data_path}")
    print(f"  Log Level          : {config.logging.level}")

    # ── 8. Full Dashboard ────────────────────────────────────────
    section("8. FULL SECURITY DASHBOARD")
    render_dashboard(resources, topology, graph_findings)

    # ── Done ─────────────────────────────────────────────────────
    section("DEMO COMPLETE")
    print("  All AeroDrift features demonstrated successfully.")
    print("  Thank you for watching!\n")


if __name__ == "__main__":
    main()
