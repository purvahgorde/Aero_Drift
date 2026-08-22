"""Tests for the drift detection foundation.

All tests use small in-memory CloudTopology graphs — no AWS credentials
or mock data files are required.
"""

import unittest

from app.graph.topology import CloudTopology
from app.graph.nodes import CloudNode
from app.detection.drift_detector import DriftDetector, DriftResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_topology(*node_specs, edges=None):
    """Build a tiny CloudTopology for testing.

    Parameters:
        node_specs: tuples of ``(resource_id, resource_type)`` or
            ``(resource_id, resource_type, name)``.
        edges: list of ``(source_id, target_id)`` tuples.
    """
    topo = CloudTopology()
    for spec in node_specs:
        rid, rtype = spec[0], spec[1]
        name = spec[2] if len(spec) > 2 else None
        topo.add_node(CloudNode(rid, rtype, name=name))
    for src, tgt in (edges or []):
        topo.add_relationship(src, tgt)
    return topo


# ---------------------------------------------------------------------------
# DriftResult unit tests
# ---------------------------------------------------------------------------

class TestDriftResult(unittest.TestCase):

    def test_default_result_is_safe(self):
        result = DriftResult()
        self.assertFalse(result.drift_detected)
        self.assertIsNone(result.source)
        self.assertIsNone(result.target)
        self.assertEqual(result.path, [])
        self.assertIsNone(result.reason)
        self.assertIsNone(result.severity)
        self.assertEqual(result.metadata, {})

    def test_to_dict_round_trip(self):
        result = DriftResult(
            drift_detected=True,
            source="a",
            target="b",
            path=["a", "b"],
            reason="test",
            severity="high",
            metadata={"k": "v"},
        )
        d = result.to_dict()
        self.assertIsInstance(d, dict)
        self.assertTrue(d["drift_detected"])
        self.assertEqual(d["source"], "a")
        self.assertEqual(d["target"], "b")
        self.assertEqual(d["path"], ["a", "b"])
        self.assertEqual(d["reason"], "test")
        self.assertEqual(d["severity"], "high")
        self.assertEqual(d["metadata"], {"k": "v"})

    def test_repr(self):
        result = DriftResult(source="x", target="y")
        r = repr(result)
        self.assertIn("DriftResult", r)
        self.assertIn("x", r)
        self.assertIn("y", r)


# ---------------------------------------------------------------------------
# DriftDetector.check_path tests
# ---------------------------------------------------------------------------

class TestCheckPath(unittest.TestCase):

    def test_no_path_returns_no_drift(self):
        """Two disconnected nodes → no drift."""
        topo = _make_topology(
            ("vpc-1", "VPC"),
            ("sg-1", "SecurityGroup"),
        )
        detector = DriftDetector(topo)
        result = detector.check_path("vpc-1", "sg-1")

        self.assertFalse(result.drift_detected)
        self.assertEqual(result.source, "vpc-1")
        self.assertEqual(result.target, "sg-1")
        self.assertEqual(result.path, [])
        self.assertIn("No path", result.reason)

    def test_path_exists_returns_drift(self):
        """Connected nodes → drift detected."""
        topo = _make_topology(
            ("vpc-1", "VPC"),
            ("subnet-1", "Subnet"),
            ("i-1", "EC2"),
            edges=[("vpc-1", "subnet-1"), ("subnet-1", "i-1")],
        )
        detector = DriftDetector(topo)
        result = detector.check_path("vpc-1", "i-1")

        self.assertTrue(result.drift_detected)
        self.assertEqual(result.source, "vpc-1")
        self.assertEqual(result.target, "i-1")
        self.assertEqual(result.path, ["vpc-1", "subnet-1", "i-1"])
        self.assertIsNotNone(result.reason)
        self.assertEqual(result.severity, "medium")

    def test_missing_source_returns_safe(self):
        topo = _make_topology(("i-1", "EC2"))
        detector = DriftDetector(topo)
        result = detector.check_path("nonexistent", "i-1")

        self.assertFalse(result.drift_detected)
        self.assertIn("not found", result.reason)
        self.assertEqual(result.metadata["status"], "source_missing")

    def test_missing_target_returns_safe(self):
        topo = _make_topology(("i-1", "EC2"))
        detector = DriftDetector(topo)
        result = detector.check_path("i-1", "nonexistent")

        self.assertFalse(result.drift_detected)
        self.assertIn("not found", result.reason)
        self.assertEqual(result.metadata["status"], "target_missing")

    def test_empty_graph_returns_safe(self):
        topo = CloudTopology()
        detector = DriftDetector(topo)
        result = detector.check_path("a", "b")

        self.assertFalse(result.drift_detected)
        self.assertEqual(result.metadata["status"], "source_missing")

    def test_custom_reason_template(self):
        topo = _make_topology(
            ("a", "VPC"),
            ("b", "Subnet"),
            edges=[("a", "b")],
        )
        detector = DriftDetector(topo)
        result = detector.check_path(
            "a", "b",
            reason_template="ALERT: {source} reaches {target}",
        )
        self.assertTrue(result.drift_detected)
        self.assertEqual(result.reason, "ALERT: a reaches b")

    def test_self_loop_path(self):
        """A node trivially reaches itself (path of length 0)."""
        topo = _make_topology(("n", "EC2"))
        detector = DriftDetector(topo)
        result = detector.check_path("n", "n")

        self.assertTrue(result.drift_detected)
        self.assertEqual(result.path, ["n"])


# ---------------------------------------------------------------------------
# detect_public_database_exposure tests
# ---------------------------------------------------------------------------

class TestDetectPublicDatabaseExposure(unittest.TestCase):

    def test_no_internet_or_db_nodes(self):
        """Graph with only VPC/Subnet/EC2/SG → safe, with explanation."""
        topo = _make_topology(
            ("vpc-1", "VPC"),
            ("sg-1", "SecurityGroup"),
            edges=[("vpc-1", "sg-1")],
        )
        detector = DriftDetector(topo)
        results = detector.detect_public_database_exposure()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].drift_detected)
        self.assertIn("missing node types", results[0].reason)
        self.assertIn("InternetGateway", results[0].metadata["missing"])
        self.assertIn("Database/RDS", results[0].metadata["missing"])

    def test_internet_present_but_no_db(self):
        topo = _make_topology(("igw-1", "InternetGateway"))
        detector = DriftDetector(topo)
        results = detector.detect_public_database_exposure()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].drift_detected)
        self.assertIn("Database/RDS", results[0].metadata["missing"])

    def test_db_present_but_no_internet(self):
        topo = _make_topology(("rds-1", "RDS"))
        detector = DriftDetector(topo)
        results = detector.detect_public_database_exposure()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].drift_detected)
        self.assertIn("InternetGateway", results[0].metadata["missing"])

    def test_both_present_no_path(self):
        """IGW and DB exist but are disconnected → safe."""
        topo = _make_topology(
            ("igw-1", "InternetGateway"),
            ("rds-1", "Database"),
        )
        detector = DriftDetector(topo)
        results = detector.detect_public_database_exposure()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].drift_detected)

    def test_both_present_with_path(self):
        """IGW → VPC → Subnet → EC2 → DB  → drift detected (high)."""
        topo = _make_topology(
            ("igw-1", "InternetGateway"),
            ("vpc-1", "VPC"),
            ("subnet-1", "Subnet"),
            ("i-1", "EC2"),
            ("rds-1", "Database"),
            edges=[
                ("igw-1", "vpc-1"),
                ("vpc-1", "subnet-1"),
                ("subnet-1", "i-1"),
                ("i-1", "rds-1"),
            ],
        )
        detector = DriftDetector(topo)
        results = detector.detect_public_database_exposure()

        drifts = [r for r in results if r.drift_detected]
        self.assertEqual(len(drifts), 1)
        self.assertEqual(drifts[0].severity, "high")
        self.assertEqual(drifts[0].source, "igw-1")
        self.assertEqual(drifts[0].target, "rds-1")
        self.assertEqual(
            drifts[0].path,
            ["igw-1", "vpc-1", "subnet-1", "i-1", "rds-1"],
        )

    def test_multiple_gateways_and_dbs(self):
        """Each (igw, db) pair is checked independently."""
        topo = _make_topology(
            ("igw-1", "InternetGateway"),
            ("igw-2", "InternetGateway"),
            ("rds-1", "RDS"),
            ("rds-2", "RDS"),
            edges=[("igw-1", "rds-1")],
        )
        detector = DriftDetector(topo)
        results = detector.detect_public_database_exposure()

        # 2 igw × 2 db = 4 checks
        self.assertEqual(len(results), 4)
        drifts = [r for r in results if r.drift_detected]
        self.assertEqual(len(drifts), 1)
        self.assertEqual(drifts[0].source, "igw-1")
        self.assertEqual(drifts[0].target, "rds-1")


# ---------------------------------------------------------------------------
# detect_cross_resource_paths tests
# ---------------------------------------------------------------------------

class TestDetectCrossResourcePaths(unittest.TestCase):

    def test_vpc_to_security_group(self):
        """Use existing resource types to verify cross-resource analysis."""
        topo = _make_topology(
            ("vpc-1", "VPC"),
            ("subnet-1", "Subnet"),
            ("i-1", "EC2"),
            ("sg-1", "SecurityGroup"),
            edges=[
                ("vpc-1", "subnet-1"),
                ("subnet-1", "i-1"),
                ("i-1", "sg-1"),
            ],
        )
        detector = DriftDetector(topo)
        results = detector.detect_cross_resource_paths("VPC", "SecurityGroup")

        drifts = [r for r in results if r.drift_detected]
        self.assertEqual(len(drifts), 1)
        self.assertEqual(
            drifts[0].path,
            ["vpc-1", "subnet-1", "i-1", "sg-1"],
        )

    def test_missing_source_type(self):
        topo = _make_topology(("sg-1", "SecurityGroup"))
        detector = DriftDetector(topo)
        results = detector.detect_cross_resource_paths("VPC", "SecurityGroup")

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].drift_detected)

    def test_missing_target_type(self):
        topo = _make_topology(("vpc-1", "VPC"))
        detector = DriftDetector(topo)
        results = detector.detect_cross_resource_paths("VPC", "SecurityGroup")

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].drift_detected)


# ---------------------------------------------------------------------------
# detect_all / detect_all_as_dicts
# ---------------------------------------------------------------------------

class TestDetectAll(unittest.TestCase):

    def test_detect_all_returns_list(self):
        topo = CloudTopology()
        detector = DriftDetector(topo)
        results = detector.detect_all()
        self.assertIsInstance(results, list)
        self.assertTrue(all(isinstance(r, DriftResult) for r in results))

    def test_detect_all_as_dicts(self):
        topo = CloudTopology()
        detector = DriftDetector(topo)
        dicts = detector.detect_all_as_dicts()
        self.assertIsInstance(dicts, list)
        self.assertTrue(all(isinstance(d, dict) for d in dicts))

    def test_detect_all_with_mock_data_topology(self):
        """Simulate the mock_aws_state.json topology.

        The mock data has: vpc-001, subnet-001, subnet-002,
        i-001 (in subnet-001, sg-001), i-002 (in subnet-002, sg-002),
        sg-001, sg-002.

        No internet or database nodes, so detect_all should report safe.
        """
        topo = _make_topology(
            ("vpc-001", "VPC", "AeroDrift-VPC"),
            ("subnet-001", "Subnet"),
            ("subnet-002", "Subnet"),
            ("i-001", "EC2", "web-server-1"),
            ("i-002", "EC2", "db-server-1"),
            ("sg-001", "SecurityGroup", "web-sg"),
            ("sg-002", "SecurityGroup", "db-sg"),
            edges=[
                ("vpc-001", "subnet-001"),
                ("vpc-001", "subnet-002"),
                ("subnet-001", "i-001"),
                ("subnet-002", "i-002"),
                ("i-001", "sg-001"),
                ("i-002", "sg-002"),
            ],
        )
        detector = DriftDetector(topo)
        results = detector.detect_all()

        self.assertTrue(len(results) >= 1)
        self.assertFalse(any(r.drift_detected for r in results))


# ---------------------------------------------------------------------------
# Helper method tests
# ---------------------------------------------------------------------------

class TestHelperMethods(unittest.TestCase):

    def test_node_exists(self):
        topo = _make_topology(("n1", "EC2"))
        detector = DriftDetector(topo)
        self.assertTrue(detector._node_exists("n1"))
        self.assertFalse(detector._node_exists("nope"))

    def test_get_node_data(self):
        topo = _make_topology(("n1", "EC2", "my-instance"))
        detector = DriftDetector(topo)
        data = detector._get_node_data("n1")
        self.assertEqual(data["resource_type"], "EC2")
        self.assertEqual(data["name"], "my-instance")
        self.assertIsNone(detector._get_node_data("nope"))

    def test_get_nodes_by_type(self):
        topo = _make_topology(
            ("v1", "VPC"),
            ("v2", "VPC"),
            ("s1", "Subnet"),
        )
        detector = DriftDetector(topo)
        vpcs = list(detector._get_nodes_by_type("VPC"))
        self.assertEqual(len(vpcs), 2)
        subnets = list(detector._get_nodes_by_type("Subnet"))
        self.assertEqual(len(subnets), 1)
        rds = list(detector._get_nodes_by_type("RDS"))
        self.assertEqual(len(rds), 0)


if __name__ == "__main__":
    unittest.main()
