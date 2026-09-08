"""Tests for the CLI command dispatch in app.main.

All tests use mock data and patched imports so no AWS credentials are needed.
"""

import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

from app.graph.topology import CloudTopology, create_network_graph
from app.graph.nodes import CloudNode


# ---------------------------------------------------------------------------
# Shared mock data (mirrors data/mock_aws_state.json)
# ---------------------------------------------------------------------------

MOCK_RESOURCES = {
    "vpcs": [
        {"id": "vpc-001", "cidr": "10.0.0.0/16", "state": "available",
         "tags": [{"Key": "Name", "Value": "AeroDrift-VPC"}]},
    ],
    "subnets": [
        {"id": "subnet-001", "vpc_id": "vpc-001", "cidr": "10.0.1.0/24"},
        {"id": "subnet-002", "vpc_id": "vpc-001", "cidr": "10.0.2.0/24"},
    ],
    "instances": [
        {"id": "i-001", "name": "web-server-1", "subnet_id": "subnet-001",
         "vpc_id": "vpc-001", "state": "running", "security_group_ids": ["sg-001"]},
        {"id": "i-002", "name": "db-server-1", "subnet_id": "subnet-002",
         "vpc_id": "vpc-001", "state": "stopped", "security_group_ids": ["sg-002"]},
    ],
    "security_groups": [
        {"id": "sg-001", "vpc_id": "vpc-001", "name": "web-sg"},
        {"id": "sg-002", "vpc_id": "vpc-001", "name": "db-sg"},
    ],
}


def _mock_collect(**_kwargs):
    """Return a copy of MOCK_RESOURCES."""
    return dict(MOCK_RESOURCES)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestCLICommands(unittest.TestCase):

    # -- helpers -----------------------------------------------------------

    def _run_main(self, argv_args):
        """Invoke app.main.main() with the given CLI args, capturing stdout."""
        import app.main as main_mod
        old_argv = sys.argv
        captured = StringIO()
        try:
            sys.argv = ["app.main"] + list(argv_args)
            with patch("sys.stdout", captured):
                main_mod.main()
        finally:
            sys.argv = old_argv
        return captured.getvalue()

    # -- summary command ---------------------------------------------------

    @patch("app.main.collect_all_resources", side_effect=_mock_collect)
    def test_summary_output(self, _mock):
        output = self._run_main(["summary"])
        self.assertIn("AERODRIFT SUMMARY", output)
        self.assertIn("VPCs", output)
        self.assertIn("Subnets", output)
        self.assertIn("EC2 Instances", output)
        self.assertIn("Security Groups", output)
        self.assertIn("Topology nodes", output)
        self.assertIn("Topology edges", output)
        self.assertIn("Status", output)

    @patch("app.main.collect_all_resources", side_effect=_mock_collect)
    def test_summary_resource_counts(self, _mock):
        output = self._run_main(["summary"])
        # 1 VPC, 2 subnets, 2 instances, 2 SGs = 7 total
        self.assertIn("Total resources    : 7", output)
        self.assertIn("VPCs               : 1", output)
        self.assertIn("Subnets            : 2", output)
        self.assertIn("EC2 Instances      : 2", output)
        self.assertIn("Security Groups    : 2", output)

    # -- topology command --------------------------------------------------

    @patch("app.main.collect_all_resources", side_effect=_mock_collect)
    @patch("app.main.render_topology")
    def test_topology_output(self, _mock_render, _mock_collect):
        output = self._run_main(["topology"])
        self.assertIn("TOPOLOGY SUMMARY", output)
        self.assertIn("Nodes", output)
        self.assertIn("Connections", output)
        self.assertIn("Node types:", output)
        # render_topology should have been called
        _mock_render.assert_called_once()

    @patch("app.main.collect_all_resources", side_effect=_mock_collect)
    @patch("app.main.render_topology")
    def test_topology_node_types(self, _mock_render, _mock_collect):
        output = self._run_main(["topology"])
        self.assertIn("VPC", output)
        self.assertIn("Subnet", output)
        self.assertIn("EC2", output)
        self.assertIn("SecurityGroup", output)

    # -- default (no args) → run full pipeline ----------------------------

    @patch("app.main.collect_all_resources", side_effect=_mock_collect)
    @patch("app.main.render_topology")
    @patch("app.main.show_summary")
    @patch("app.main.show_welcome")
    def test_default_runs_full_pipeline(self, mock_welcome, mock_summary,
                                        mock_render, _mock_collect):
        self._run_main([])
        mock_welcome.assert_called_once()
        mock_summary.assert_called_once()
        mock_render.assert_called_once()

    # -- unknown command ---------------------------------------------------

    @patch("app.main.collect_all_resources", side_effect=_mock_collect)
    def test_unknown_command_prints_error(self, _mock):
        import app.main as main_mod
        captured_err = StringIO()
        old_argv = sys.argv
        try:
            sys.argv = ["app.main", "invalid_command"]
            with patch("sys.stderr", captured_err):
                with self.assertRaises(SystemExit) as ctx:
                    main_mod.main()
                self.assertEqual(ctx.exception.code, 1)
        finally:
            sys.argv = old_argv
        err_output = captured_err.getvalue()
        self.assertIn("unknown command", err_output)

    # -- help command ------------------------------------------------------

    def test_help_command(self):
        output = self._run_main(["--help"])
        self.assertIn("AeroDrift CLI", output)
        self.assertIn("summary", output)
        self.assertIn("topology", output)

    def test_help_word(self):
        output = self._run_main(["help"])
        self.assertIn("Usage:", output)

    # -- case insensitivity ------------------------------------------------

    @patch("app.main.collect_all_resources", side_effect=_mock_collect)
    def test_command_case_insensitive(self, _mock):
        output = self._run_main(["SUMMARY"])
        self.assertIn("AERODRIFT SUMMARY", output)

    # -- error handling: collect failure -----------------------------------

    @patch("app.main.collect_all_resources",
           side_effect=Exception("AWS unavailable"))
    def test_summary_handles_collect_error(self, _mock):
        captured_err = StringIO()
        with patch("sys.stderr", captured_err):
            output = self._run_main(["summary"])
        err_output = captured_err.getvalue()
        self.assertIn("Error collecting resources", err_output)

    # -- empty resources ---------------------------------------------------

    @patch("app.main.collect_all_resources",
           return_value={"vpcs": [], "subnets": [], "instances": [], "security_groups": []})
    def test_summary_with_empty_resources(self, _mock):
        output = self._run_main(["summary"])
        self.assertIn("AERODRIFT SUMMARY", output)
        self.assertIn("Total resources    : 0", output)

    # -- config command ----------------------------------------------------

    def test_config_output(self):
        output = self._run_main(["config"])
        self.assertIn("AERODRIFT CONFIGURATION", output)
        self.assertIn("App Name", output)
        self.assertIn("AeroDrift", output)
        self.assertIn("AWS Region", output)
        self.assertIn("us-east-1", output)
        self.assertIn("Log Level", output)

    # -- security command --------------------------------------------------

    @patch("app.main.collect_all_resources", side_effect=_mock_collect)
    def test_security_output(self, _mock):
        output = self._run_main(["security"])
        self.assertIn("SECURITY FINDINGS", output)

    @patch("app.main.collect_all_resources",
           return_value={"vpcs": [], "subnets": [], "instances": [], "security_groups": []})
    def test_security_no_findings(self, _mock):
        output = self._run_main(["security"])
        self.assertIn("SECURITY FINDINGS", output)
        self.assertIn("SECURE", output)

    # -- drift command -----------------------------------------------------

    def test_drift_output(self):
        output = self._run_main(["drift"])
        self.assertIn("DRIFT DETECTION RESULTS", output)
        self.assertIn("Nodes added", output)
        self.assertIn("Nodes removed", output)
        self.assertIn("Nodes changed", output)
        self.assertIn("DRIFT DETECTED", output)

    # -- scan command ------------------------------------------------------

    @patch("app.main.collect_all_resources", side_effect=_mock_collect)
    def test_scan_output(self, _mock):
        output = self._run_main(["scan"])
        self.assertIn("AERODRIFT", output)

    # -- help includes new commands ----------------------------------------

    def test_help_shows_all_commands(self):
        output = self._run_main(["--help"])
        self.assertIn("security", output)
        self.assertIn("drift", output)
        self.assertIn("config", output)
        self.assertIn("scan", output)


if __name__ == "__main__":
    unittest.main()
