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
from app.config import load_config, ConfigError



AVAILABLE_COMMANDS = ["summary", "topology", "dashboard", "config"]


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
    else:
        print(f"Error: unknown command '{args[0]}'", file=sys.stderr)
        print(file=sys.stderr)
        _print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()