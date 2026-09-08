import sys
import os

# Ensure project root is in sys.path when executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.dashboard.cli import show_welcome, render_dashboard
from app.dashboard.summary import show_summary
from app.dashboard.topology_view import render_topology
from app.ingestion.collector import collect_all_resources
from app.graph.topology import create_network_graph
from app.graph.builder import build_cloud_graph
from app.graph.drift_detector import detect_public_database_exposure
from app.detection.security_analysis import detect_security_findings
from app.detection.drift_detector import detect_drift
from app.config import load_config, ConfigError
from app.persistence.database import AeroDriftDB, DatabaseError
from app.persistence.models import compare_scans, build_drift_summary



AVAILABLE_COMMANDS = ["summary", "topology", "dashboard", "config", "security", "drift", "scan", "history"]


def _collect_and_build():
    """Collect cloud resources and build the topology graph.

    Returns (resources, topology) or prints an error and returns (None, None).
    """
    try:
        resources = collect_all_resources()
    except Exception as exc:
        print(f"Error collecting resources: {exc}", file=sys.stderr)
        return None, None

    if not resources or all(len(v) == 0 for v in resources.values()):
        print("Warning: no resources found. Using empty dataset.")

    try:
        topology = create_network_graph(resources)
    except Exception as exc:
        print(f"Error building topology: {exc}", file=sys.stderr)
        return resources, None

    return resources, topology


def _run_security_analysis(resources, topology):
    """Run all available security detection and return combined findings.

    Returns a list of finding dicts.  Never raises — returns [] on error.
    """
    findings = []

    # 1. Member 2's security analysis (detect_security_findings)
    try:
        sa_findings = detect_security_findings(topology, resources)
        if sa_findings:
            findings.extend(sa_findings)
    except Exception:
        pass  # graceful degradation

    # 2. Member 3's graph-based detection (detect_public_database_exposure)
    try:
        cloud_graph = build_cloud_graph(resources)
        graph_findings = detect_public_database_exposure(cloud_graph)
        if graph_findings:
            # Avoid exact duplicates by checking resource_id
            existing_ids = {
                (f.get("resource_id") or f.get("instance_id"), f.get("reason"))
                for f in findings
            }
            for gf in graph_findings:
                key = (gf.get("resource_id"), gf.get("reason"))
                if key not in existing_ids:
                    findings.append(gf)
    except Exception:
        pass  # graceful degradation

    return findings


def run():
    """Run the full AeroDrift pipeline (original behaviour)."""
    show_welcome()

    resources, topology = _collect_and_build()
    if resources is None:
        return None, None

    show_summary(resources)

    if topology is not None:
        render_topology(topology)

    return resources, topology


def cmd_summary():
    """Display a high-level infrastructure summary."""
    resources, topology = _collect_and_build()
    if resources is None:
        return

    graph_info = topology.get_graph_summary() if topology else {"nodes": 0, "edges": 0}

    total_resources = sum(len(v) for v in resources.values())

    print("=" * 40)
    print("        AERODRIFT SUMMARY")
    print("=" * 40)
    print()
    print(f"  VPCs               : {len(resources.get('vpcs', []))}")
    print(f"  Subnets            : {len(resources.get('subnets', []))}")
    print(f"  EC2 Instances      : {len(resources.get('instances', resources.get('ec2', [])))}")
    print(f"  Security Groups    : {len(resources.get('security_groups', []))}")
    print(f"  Total resources    : {total_resources}")
    print()
    print(f"  Topology nodes     : {graph_info['nodes']}")
    print(f"  Topology edges     : {graph_info['edges']}")
    print()
    print(f"  Status: HEALTHY")
    print("=" * 40)


def cmd_topology():
    """Display a topology summary and tree view."""
    resources, topology = _collect_and_build()
    if resources is None:
        return
    if topology is None:
        print("Error: could not build topology.", file=sys.stderr)
        return

    graph_info = topology.get_graph_summary()
    nodes = topology.get_nodes()

    # Count node types
    type_counts = {}
    for _, data in nodes:
        rtype = data.get("resource_type", "Unknown")
        type_counts[rtype] = type_counts.get(rtype, 0) + 1

    print("=" * 40)
    print("       TOPOLOGY SUMMARY")
    print("=" * 40)
    print()
    print(f"  Nodes       : {graph_info['nodes']}")
    print(f"  Connections : {graph_info['edges']}")
    print()
    print("  Node types:")
    for rtype in sorted(type_counts):
        print(f"    {rtype:<18}: {type_counts[rtype]}")
    print()
    print("=" * 40)
    print()

    render_topology(topology)


def cmd_dashboard():
    """Display the full modern CLI dashboard with interactive menu."""
    resources, topology = _collect_and_build()
    if resources is None:
        return

    # Run security analysis
    findings = []
    if topology is not None:
        findings = _run_security_analysis(resources, topology)

    render_dashboard(resources, topology, findings)

    # Interactive menu loop
    while True:
        try:
            choice = input("\n  Select action ([1-4] or [Q]): ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice == "Q":
            break
        elif choice == "1":
            # Re-scan infrastructure and refresh dashboard
            print()
            resources, topology = _collect_and_build()
            if resources is None:
                continue
            findings = []
            if topology is not None:
                findings = _run_security_analysis(resources, topology)
            render_dashboard(resources, topology, findings)
        elif choice == "2":
            # View security findings detail
            print()
            from app.dashboard.audit import show_drift_findings
            show_drift_findings(findings)
        elif choice == "3":
            # View topology tree
            print()
            if topology is not None:
                render_topology(topology)
            else:
                print("  Topology data not available.")
        elif choice == "4":
            # View remediation details
            print()
            from app.dashboard.cli import _render_remediation, _get_dashboard_width
            from app.dashboard.cli import console as cli_console
            width = _get_dashboard_width(cli_console)
            _render_remediation(findings, cli_console, width)
        else:
            print(f"  Unknown option: {choice}")


def cmd_config():
    """Display the current AeroDrift configuration."""
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Error loading configuration: {exc}", file=sys.stderr)
        return

    print("=" * 40)
    print("     AERODRIFT CONFIGURATION")
    print("=" * 40)
    print()
    print(f"  App Name           : {config.app.name}")
    print(f"  Description        : {config.app.description}")
    print(f"  Version            : {config.app.version}")
    print()
    print(f"  AWS Region         : {config.aws.region}")
    print(f"  Mock Data Path     : {config.aws.mock_data_path}")
    print()
    print(f"  Log Level          : {config.logging.level}")
    print(f"  Verbose            : {config.logging.verbose}")
    print()
    print("=" * 40)


def cmd_security():
    """Display standalone security findings."""
    resources, topology = _collect_and_build()
    if resources is None:
        return

    findings = []
    if topology is not None:
        findings = _run_security_analysis(resources, topology)

    print("=" * 40)
    print("     SECURITY FINDINGS")
    print("=" * 40)
    print()

    if not findings:
        print("  No security findings detected.")
        print()
        print("  Status: SECURE")
    else:
        for i, finding in enumerate(findings, 1):
            severity = finding.get("severity", "UNKNOWN")
            resource = (
                finding.get("resource_name")
                or finding.get("resource_id")
                or finding.get("instance_id")
                or "Unknown"
            )
            reason = finding.get("reason", "Security issue detected")
            sgs = finding.get("security_groups", [])
            path = finding.get("path", [])

            print(f"  [{i}] [{severity}] {resource}")
            print(f"      Reason : {reason}")
            if sgs:
                print(f"      SGs    : {', '.join(sgs)}")
            if path:
                print(f"      Path   : {' -> '.join(str(p) for p in path)}")
            print()

        high_count = sum(
            1 for f in findings
            if f.get("severity", "").upper() in ("HIGH", "CRITICAL")
        )
        print(f"  Total findings : {len(findings)}")
        print(f"  High/Critical  : {high_count}")

    print()
    print("=" * 40)


def cmd_drift():
    """Demonstrate drift detection between two topology snapshots."""
    from app.graph.topology import CloudTopology
    from app.graph.nodes import CloudNode

    # Build a "previous" topology snapshot
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

    # Build a "current" topology snapshot with changes
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

    # Detect drift
    drift = detect_drift(previous, current)

    print("=" * 40)
    print("     DRIFT DETECTION RESULTS")
    print("=" * 40)
    print()

    # Node changes
    added = drift["nodes"]["added"]
    removed = drift["nodes"]["removed"]
    changed = drift["nodes"]["changed"]

    print(f"  Nodes added    : {len(added)}")
    if added:
        for node_id in added:
            print(f"    + {node_id}")

    print(f"  Nodes removed  : {len(removed)}")
    if removed:
        for node_id in removed:
            print(f"    - {node_id}")

    print(f"  Nodes changed  : {len(changed)}")
    if changed:
        for change in changed:
            print(f"    ~ {change['resource_id']}")
            for attr, vals in change["changes"].items():
                print(f"        {attr}: {vals['previous']} -> {vals['current']}")

    print()

    # Relationship changes
    rel_added = drift["relationships"]["added"]
    rel_removed = drift["relationships"]["removed"]

    print(f"  Edges added    : {len(rel_added)}")
    if rel_added:
        for src, dst in rel_added:
            print(f"    + {src} -> {dst}")

    print(f"  Edges removed  : {len(rel_removed)}")
    if rel_removed:
        for src, dst in rel_removed:
            print(f"    - {src} -> {dst}")

    print()

    total_changes = len(added) + len(removed) + len(changed) + len(rel_added) + len(rel_removed)
    if total_changes == 0:
        print("  Status: NO DRIFT DETECTED")
    else:
        print(f"  Status: DRIFT DETECTED ({total_changes} change(s))")

    print("=" * 40)


def cmd_scan():
    """Quick scan: collect, analyse, and display results (non-interactive)."""
    resources, topology = _collect_and_build()
    if resources is None:
        return

    # Run security analysis
    findings = []
    if topology is not None:
        findings = _run_security_analysis(resources, topology)

    render_dashboard(resources, topology, findings)


def _print_usage():
    """Print CLI usage help."""
    print("=" * 40)
    print("  AeroDrift CLI")
    print("=" * 40)
    print()
    print("Usage:")
    print("  python -m app.main              Run full pipeline")
    print("  python -m app.main summary      Infrastructure summary")
    print("  python -m app.main topology     Topology summary and tree")
    print("  python -m app.main dashboard    Full security dashboard")
    print("  python -m app.main security     Security findings report")
    print("  python -m app.main drift        Drift detection demo")
    print("  python -m app.main config       Show configuration")
    print("  python -m app.main scan         Quick scan (non-interactive)")
    print()
    print(f"Available commands: {', '.join(AVAILABLE_COMMANDS)}")
    print("=" * 40)


def main():
    """CLI entry point with command dispatch."""
    args = sys.argv[1:]

    if not args:
        # Preserve original behaviour: run full pipeline
        run()
        return

    command = args[0].lower()

    if command in ("--help", "-h", "help"):
        _print_usage()
    elif command == "summary":
        cmd_summary()
    elif command == "topology":
        cmd_topology()
    elif command == "dashboard":
        cmd_dashboard()
    elif command == "config":
        cmd_config()
    elif command == "security":
        cmd_security()
    elif command == "drift":
        cmd_drift()
    elif command == "scan":
        cmd_scan()
    else:
        print(f"Error: unknown command '{args[0]}'", file=sys.stderr)
        print(file=sys.stderr)
        _print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()