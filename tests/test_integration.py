"""Week 1 integration tests for AeroDrift.

Verifies the complete end-to-end flow:

    Mock AWS Data  →  Ingestion  →  Structured State  →  NetworkX Topology  →  Rich Dashboard

All tests use the mock data file (data/mock_aws_state.json) so no AWS
credentials are required.
"""

import json
import os
import unittest
from io import StringIO
from unittest.mock import patch

from app.ingestion.collector import collect_all_resources
from app.graph.topology import create_network_graph, CloudTopology
from app.dashboard.summary import show_summary
from app.dashboard.topology_view import render_topology
from app.dashboard.cli import show_welcome


# ---------------------------------------------------------------------------
# Path to mock data
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
_MOCK_DATA_PATH = os.path.join(_PROJECT_ROOT, "data", "mock_aws_state.json")


def _load_mock_data():
    """Load and return the mock AWS state from the JSON fixture."""
    with open(_MOCK_DATA_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# A. Mock data loading
# ---------------------------------------------------------------------------

class TestMockDataLoading(unittest.TestCase):
    """Verify that the mock infrastructure data file can be loaded."""

    def test_mock_file_exists(self):
        self.assertTrue(
            os.path.isfile(_MOCK_DATA_PATH),
            f"Mock data file not found at {_MOCK_DATA_PATH}",
        )

    def test_mock_data_is_valid_json(self):
        data = _load_mock_data()
        self.assertIsInstance(data, dict)

    def test_mock_data_has_required_keys(self):
        data = _load_mock_data()
        for key in ("vpcs", "subnets", "instances", "security_groups"):
            self.assertIn(key, data, f"Mock data missing key: {key}")

    def test_mock_data_has_resources(self):
        data = _load_mock_data()
        self.assertGreater(len(data["vpcs"]), 0)
        self.assertGreater(len(data["subnets"]), 0)
        self.assertGreater(len(data["instances"]), 0)
        self.assertGreater(len(data["security_groups"]), 0)


# ---------------------------------------------------------------------------
# B. Ingestion → structured data
# ---------------------------------------------------------------------------

class TestIngestionProducesStructuredData(unittest.TestCase):
    """Verify that the ingestion layer produces the expected structured
    resource representation when AWS is unavailable (mock fallback)."""

    def test_collect_all_resources_returns_dict(self):
        resources = collect_all_resources()
        self.assertIsInstance(resources, dict)

    def test_collected_resources_have_required_keys(self):
        resources = collect_all_resources()
        for key in ("vpcs", "subnets", "instances", "security_groups"):
            self.assertIn(key, resources)

    def test_collected_resources_are_non_empty(self):
        resources = collect_all_resources()
        total = sum(len(v) for v in resources.values())
        self.assertGreater(total, 0, "Ingestion returned zero resources")


# ---------------------------------------------------------------------------
# C. Structured data → NetworkX topology
# ---------------------------------------------------------------------------

class TestTopologyFromMockData(unittest.TestCase):
    """Verify that mock data can be passed into the topology layer and
    produces a valid graph."""

    def setUp(self):
        self.resources = _load_mock_data()
        self.topology = create_network_graph(self.resources)

    def test_returns_cloud_topology(self):
        self.assertIsInstance(self.topology, CloudTopology)

    def test_graph_is_non_empty(self):
        summary = self.topology.get_graph_summary()
        self.assertGreater(summary["nodes"], 0, "Graph has no nodes")
        self.assertGreater(summary["edges"], 0, "Graph has no edges")

    def test_expected_node_count(self):
        # 1 VPC + 2 subnets + 2 EC2 + 2 SGs = 7
        summary = self.topology.get_graph_summary()
        self.assertEqual(summary["nodes"], 7)

    def test_expected_edge_count(self):
        # VPC→subnet-001, VPC→subnet-002,
        # subnet-001→i-001, subnet-002→i-002,
        # i-001→sg-001, i-002→sg-002 = 6
        summary = self.topology.get_graph_summary()
        self.assertEqual(summary["edges"], 6)


# ---------------------------------------------------------------------------
# D. Graph relationship verification
# ---------------------------------------------------------------------------

class TestGraphRelationships(unittest.TestCase):
    """Verify that the expected nodes and edges are present."""

    def setUp(self):
        self.resources = _load_mock_data()
        self.topology = create_network_graph(self.resources)
        self.graph = self.topology.graph

    def test_vpc_node_exists(self):
        self.assertIn("vpc-001", self.graph)

    def test_subnet_nodes_exist(self):
        self.assertIn("subnet-001", self.graph)
        self.assertIn("subnet-002", self.graph)

    def test_ec2_nodes_exist(self):
        self.assertIn("i-001", self.graph)
        self.assertIn("i-002", self.graph)

    def test_security_group_nodes_exist(self):
        self.assertIn("sg-001", self.graph)
        self.assertIn("sg-002", self.graph)

    def test_vpc_to_subnet_edges(self):
        self.assertTrue(self.graph.has_edge("vpc-001", "subnet-001"))
        self.assertTrue(self.graph.has_edge("vpc-001", "subnet-002"))

    def test_subnet_to_ec2_edges(self):
        self.assertTrue(self.graph.has_edge("subnet-001", "i-001"))
        self.assertTrue(self.graph.has_edge("subnet-002", "i-002"))

    def test_ec2_to_sg_edges(self):
        self.assertTrue(self.graph.has_edge("i-001", "sg-001"))
        self.assertTrue(self.graph.has_edge("i-002", "sg-002"))

    def test_node_types(self):
        self.assertEqual(self.graph.nodes["vpc-001"]["resource_type"], "VPC")
        self.assertEqual(self.graph.nodes["subnet-001"]["resource_type"], "Subnet")
        self.assertEqual(self.graph.nodes["i-001"]["resource_type"], "EC2")
        self.assertEqual(self.graph.nodes["sg-001"]["resource_type"], "SecurityGroup")

    def test_path_vpc_to_sg(self):
        path = self.topology.find_path("vpc-001", "sg-001")
        self.assertEqual(path, ["vpc-001", "subnet-001", "i-001", "sg-001"])


# ---------------------------------------------------------------------------
# E. Dashboard / CLI does not crash
# ---------------------------------------------------------------------------

class TestDashboardConsumesTopology(unittest.TestCase):
    """Verify that the dashboard layer can consume the topology without
    crashing."""

    def setUp(self):
        self.resources = _load_mock_data()
        self.topology = create_network_graph(self.resources)

    def test_show_welcome_runs(self):
        # Capture output to avoid polluting test runner
        with patch("sys.stdout", new_callable=StringIO):
            show_welcome()  # should not raise

    def test_show_summary_runs(self):
        with patch("sys.stdout", new_callable=StringIO):
            show_summary(self.resources)  # should not raise

    def test_render_topology_runs(self):
        with patch("sys.stdout", new_callable=StringIO):
            render_topology(self.topology)  # should not raise


# ---------------------------------------------------------------------------
# F. Full end-to-end flow
# ---------------------------------------------------------------------------

class TestEndToEndFlow(unittest.TestCase):
    """Execute the complete Week 1 flow:

        mock data → ingestion → structured state → topology → CLI/dashboard
    """

    def test_full_mock_flow(self):
        # 1. Load mock data
        mock_data = _load_mock_data()
        self.assertIsInstance(mock_data, dict)

        # 2. Ingestion (use mock data directly as structured state)
        resources = mock_data
        self.assertIn("vpcs", resources)
        self.assertIn("instances", resources)

        # 3. Build topology
        topology = create_network_graph(resources)
        self.assertIsInstance(topology, CloudTopology)

        summary = topology.get_graph_summary()
        self.assertGreater(summary["nodes"], 0)
        self.assertGreater(summary["edges"], 0)

        # 4. Feed into dashboard (capture output, verify no crash)
        with patch("sys.stdout", new_callable=StringIO):
            show_welcome()
            show_summary(resources)
            render_topology(topology)

    def test_full_collector_flow(self):
        """End-to-end through the actual collector (with AWS fallback)."""
        # 1. Ingestion via collector (falls back to mock JSON)
        resources = collect_all_resources()
        self.assertIsInstance(resources, dict)
        total = sum(len(v) for v in resources.values())
        self.assertGreater(total, 0)

        # 2. Topology
        topology = create_network_graph(resources)
        summary = topology.get_graph_summary()
        self.assertGreater(summary["nodes"], 0)

        # 3. Dashboard
        with patch("sys.stdout", new_callable=StringIO):
            show_welcome()
            show_summary(resources)
            render_topology(topology)


if __name__ == "__main__":
    unittest.main()
