"""Tests for the NetworkX topology module (app.graph.topology).

Verifies CloudTopology graph construction, node/edge management,
path finding, and graph summary reporting.
"""

import unittest

from app.graph.topology import CloudTopology, create_network_graph
from app.graph.nodes import CloudNode


class TestCloudTopologyConstruction(unittest.TestCase):
    """Test that nodes and edges are added correctly."""

    def setUp(self):
        self.topology = CloudTopology()

        self.topology.add_node(CloudNode("vpc-001", "VPC", "main-vpc"))
        self.topology.add_node(CloudNode("subnet-001", "Subnet", "private-subnet"))
        self.topology.add_node(CloudNode("i-12345", "EC2", "web-server"))
        self.topology.add_node(CloudNode("db-001", "Database", "private-db"))

        self.topology.add_relationship("vpc-001", "subnet-001")
        self.topology.add_relationship("subnet-001", "i-12345")
        self.topology.add_relationship("i-12345", "db-001")

    def test_node_count(self):
        assert self.topology.graph.number_of_nodes() == 4

    def test_edge_count(self):
        assert self.topology.graph.number_of_edges() == 3

    def test_nodes_present(self):
        assert "vpc-001" in self.topology.graph
        assert "subnet-001" in self.topology.graph
        assert "i-12345" in self.topology.graph
        assert "db-001" in self.topology.graph

    def test_node_attributes(self):
        assert self.topology.graph.nodes["i-12345"]["resource_type"] == "EC2"
        assert self.topology.graph.nodes["i-12345"]["name"] == "web-server"

    def test_forward_edges_exist(self):
        assert self.topology.graph.has_edge("vpc-001", "subnet-001")
        assert self.topology.graph.has_edge("subnet-001", "i-12345")
        assert self.topology.graph.has_edge("i-12345", "db-001")

    def test_reverse_edges_absent(self):
        assert not self.topology.graph.has_edge("subnet-001", "vpc-001")
        assert not self.topology.graph.has_edge("i-12345", "subnet-001")
        assert not self.topology.graph.has_edge("db-001", "i-12345")


class TestCloudTopologyPathFinding(unittest.TestCase):
    """Test shortest-path queries on the directed graph."""

    def setUp(self):
        self.topology = CloudTopology()

        self.topology.add_node(CloudNode("vpc-001", "VPC", "main-vpc"))
        self.topology.add_node(CloudNode("subnet-001", "Subnet", "private-subnet"))
        self.topology.add_node(CloudNode("i-12345", "EC2", "web-server"))
        self.topology.add_node(CloudNode("db-001", "Database", "private-db"))

        self.topology.add_relationship("vpc-001", "subnet-001")
        self.topology.add_relationship("subnet-001", "i-12345")
        self.topology.add_relationship("i-12345", "db-001")

    def test_full_path(self):
        path = self.topology.find_path("vpc-001", "db-001")
        assert path == ["vpc-001", "subnet-001", "i-12345", "db-001"]

    def test_partial_path(self):
        path = self.topology.find_path("vpc-001", "i-12345")
        assert path == ["vpc-001", "subnet-001", "i-12345"]

    def test_reverse_path_returns_none(self):
        path = self.topology.find_path("db-001", "vpc-001")
        assert path is None

    def test_direct_path(self):
        path = self.topology.find_path("i-12345", "db-001")
        assert path == ["i-12345", "db-001"]


class TestCloudTopologyAccessors(unittest.TestCase):
    """Test get_nodes, get_edges, and get_graph_summary."""

    def setUp(self):
        self.topology = CloudTopology()

        self.topology.add_node(CloudNode("vpc-001", "VPC", "main-vpc"))
        self.topology.add_node(CloudNode("subnet-001", "Subnet", "private-subnet"))
        self.topology.add_node(CloudNode("i-12345", "EC2", "web-server"))
        self.topology.add_node(CloudNode("db-001", "Database", "private-db"))

        self.topology.add_relationship("vpc-001", "subnet-001")
        self.topology.add_relationship("subnet-001", "i-12345")
        self.topology.add_relationship("i-12345", "db-001")

    def test_get_nodes(self):
        nodes = self.topology.get_nodes()
        assert len(nodes) == 4

    def test_get_edges(self):
        edges = self.topology.get_edges()
        assert len(edges) == 3

    def test_get_graph_summary(self):
        summary = self.topology.get_graph_summary()
        assert summary == {"nodes": 4, "edges": 3}


if __name__ == "__main__":
    unittest.main()