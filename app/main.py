import sys
import os

# Ensure project root is in sys.path when executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.dashboard.cli import show_welcome
from app.dashboard.summary import show_summary
from app.dashboard.topology_view import render_topology
from app.ingestion.collector import collect_all_resources
from app.graph.topology import create_network_graph


def run():
    show_welcome()

    resources = collect_all_resources()

    show_summary(resources)

    topology = create_network_graph(resources)

    render_topology(topology)

    return resources, topology


if __name__ == "__main__":
    run()