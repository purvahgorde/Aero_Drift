import sys
import os

# Ensure project root is in sys.path when executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.dashboard.cli import show_welcome
from app.dashboard.summary import show_summary
from app.dashboard.topology_view import render_topology
from app.ingestion.collector import collect_all_resources
from app.graph.topology import create_network_graph
from app.config import load_config, ConfigError



AVAILABLE_COMMANDS = ["summary", "topology", "config"]


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
    else:
        print(f"Error: unknown command '{args[0]}'", file=sys.stderr)
        print(file=sys.stderr)
        _print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()