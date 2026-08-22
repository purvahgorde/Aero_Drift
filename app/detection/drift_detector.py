"""Drift detection foundation for AeroDrift.

Consumes the existing CloudTopology / NetworkX graph to analyse reachability
between cloud resources.  The detector is intentionally designed around the
*current* graph API (find_path, get_nodes, get_edges) so that no second graph
is created.

Currently available resource types in the graph:
    VPC, Subnet, EC2, SecurityGroup

Future commits will add:
    - Internet gateway / 0.0.0.0/0 ingress nodes
    - Database (RDS) nodes
    - Security-group-rule edge attributes
    - Remediation actions

Missing data required for full Internet -> Database exposure detection:
    1. An "internet" source node representing 0.0.0.0/0 ingress.
    2. Database / RDS target nodes.
    3. Security-group rule CIDR data attached to graph edges or node
       attributes (the ingestion layer already collects this data via
       ``app.ingestion.rules.parse_ingress_rules``; it just isn't wired
       into the topology graph yet).
"""


class DriftResult:
    """Structured result returned by every drift detection check.

    Attributes:
        drift_detected (bool): Whether a security drift was found.
        source (str | None): The source node ID involved, if any.
        target (str | None): The target node ID involved, if any.
        path (list[str]): The network path connecting source to target.
        reason (str | None): Human-readable explanation of the finding.
        severity (str | None): "high", "medium", "low", or None.
        metadata (dict): Arbitrary extra context for downstream consumers.
    """

    def __init__(
        self,
        drift_detected=False,
        source=None,
        target=None,
        path=None,
        reason=None,
        severity=None,
        metadata=None,
    ):
        self.drift_detected = drift_detected
        self.source = source
        self.target = target
        self.path = path if path is not None else []
        self.reason = reason
        self.severity = severity
        self.metadata = metadata if metadata is not None else {}

    def to_dict(self):
        """Serialise to a plain dictionary."""
        return {
            "drift_detected": self.drift_detected,
            "source": self.source,
            "target": self.target,
            "path": self.path,
            "reason": self.reason,
            "severity": self.severity,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return (
            f"DriftResult(drift_detected={self.drift_detected}, "
            f"source={self.source!r}, target={self.target!r}, "
            f"path={self.path}, reason={self.reason!r})"
        )


class DriftDetector:
    """Cloud drift detector that operates on an existing CloudTopology.

    Usage::

        from app.graph.topology import create_network_graph, CloudTopology
        from app.detection.drift_detector import DriftDetector

        topology = create_network_graph(resources)
        detector = DriftDetector(topology)
        results  = detector.detect_all()

    Parameters:
        topology: A ``CloudTopology`` instance (or any object exposing
                  ``.find_path()``, ``.get_nodes()``, ``.get_edges()``,
                  and ``.graph``).
    """

    def __init__(self, topology):
        self.topology = topology

    # ------------------------------------------------------------------
    # Node helpers
    # ------------------------------------------------------------------

    def _node_exists(self, node_id):
        """Return True if *node_id* is present in the topology graph."""
        return node_id in self.topology.graph

    def _get_node_data(self, node_id):
        """Return the attribute dict for *node_id*, or None."""
        if not self._node_exists(node_id):
            return None
        return dict(self.topology.graph.nodes[node_id])

    def _get_nodes_by_type(self, resource_type):
        """Yield ``(node_id, data_dict)`` for every node of the given type."""
        for node_id, data in self.topology.get_nodes():
            if data.get("resource_type") == resource_type:
                yield node_id, data

    # ------------------------------------------------------------------
    # Core reachability check
    # ------------------------------------------------------------------

    def check_path(self, source_id, target_id, reason_template=None):
        """Check whether a directed path exists from *source_id* to *target_id*.

        Returns a ``DriftResult``.  When either node is missing the result
        indicates *no drift* and includes a descriptive reason so that
        callers can distinguish "safe" from "unable to check".

        Parameters:
            source_id: Starting node in the topology.
            target_id: Destination node in the topology.
            reason_template: Optional format-string used when a path is
                found.  Receives ``{source}``, ``{target}``, and
                ``{path}`` as keyword arguments.
        """
        # --- guard: source missing ---
        if not self._node_exists(source_id):
            return DriftResult(
                drift_detected=False,
                source=source_id,
                target=target_id,
                reason=f"Source node '{source_id}' not found in topology",
                metadata={"check": "path", "status": "source_missing"},
            )

        # --- guard: target missing ---
        if not self._node_exists(target_id):
            return DriftResult(
                drift_detected=False,
                source=source_id,
                target=target_id,
                reason=f"Target node '{target_id}' not found in topology",
                metadata={"check": "path", "status": "target_missing"},
            )

        path = self.topology.find_path(source_id, target_id)

        if path is None:
            return DriftResult(
                drift_detected=False,
                source=source_id,
                target=target_id,
                reason=f"No path from '{source_id}' to '{target_id}'",
                metadata={"check": "path", "status": "no_path"},
            )

        # Path exists — potential drift.
        if reason_template:
            reason = reason_template.format(
                source=source_id, target=target_id, path=path,
            )
        else:
            reason = (
                f"Reachable path found from '{source_id}' to '{target_id}'"
            )

        return DriftResult(
            drift_detected=True,
            source=source_id,
            target=target_id,
            path=path,
            reason=reason,
            severity="medium",
            metadata={"check": "path", "status": "path_found"},
        )

    # ------------------------------------------------------------------
    # Targeted detection checks
    # ------------------------------------------------------------------

    def detect_public_database_exposure(self):
        """Detect whether any internet-facing source can reach a database.

        Currently the topology does **not** contain internet-gateway or
        database/RDS nodes.  This method is therefore a forward-looking
        stub that:

        1. Searches for nodes whose ``resource_type`` indicates an
           internet entry-point (e.g. ``"InternetGateway"``).
        2. Searches for nodes whose ``resource_type`` indicates a
           database (e.g. ``"Database"``, ``"RDS"``).
        3. Runs ``check_path`` for every (gateway, db) pair found.

        When the required node types are not yet ingested it returns a
        single safe ``DriftResult`` explaining why no check was performed.

        Returns:
            list[DriftResult]
        """
        # Collect internet-facing source nodes.
        # Accept several possible type names to be resilient to future
        # ingestion naming conventions.
        internet_types = {"InternetGateway", "IGW", "Internet"}
        internet_nodes = []
        for node_id, data in self.topology.get_nodes():
            if data.get("resource_type") in internet_types:
                internet_nodes.append(node_id)

        # Collect database target nodes.
        database_types = {"Database", "RDS", "DBInstance"}
        database_nodes = []
        for node_id, data in self.topology.get_nodes():
            if data.get("resource_type") in database_types:
                database_nodes.append(node_id)

        # If either set is empty we cannot perform the check.
        if not internet_nodes or not database_nodes:
            missing = []
            if not internet_nodes:
                missing.append("InternetGateway")
            if not database_nodes:
                missing.append("Database/RDS")
            return [
                DriftResult(
                    drift_detected=False,
                    reason=(
                        "Cannot check public database exposure: "
                        f"missing node types in topology: {', '.join(missing)}"
                    ),
                    metadata={
                        "check": "public_db_exposure",
                        "status": "missing_node_types",
                        "missing": missing,
                    },
                )
            ]

        results = []
        for src in internet_nodes:
            for tgt in database_nodes:
                result = self.check_path(
                    src,
                    tgt,
                    reason_template=(
                        "Public database exposure: path exists from "
                        "'{source}' to '{target}' via {path}"
                    ),
                )
                if result.drift_detected:
                    result.severity = "high"
                    result.metadata["check"] = "public_db_exposure"
                results.append(result)

        return results

    def detect_cross_resource_paths(self, source_type, target_type):
        """Find all directed paths between nodes of *source_type* and *target_type*.

        Useful for ad-hoc reachability analysis using existing resource
        types (VPC, Subnet, EC2, SecurityGroup).

        Returns:
            list[DriftResult]
        """
        sources = list(self._get_nodes_by_type(source_type))
        targets = list(self._get_nodes_by_type(target_type))

        if not sources or not targets:
            return [
                DriftResult(
                    drift_detected=False,
                    reason=(
                        f"No nodes of type '{source_type}' or "
                        f"'{target_type}' found in topology"
                    ),
                    metadata={
                        "check": "cross_resource_paths",
                        "status": "missing_node_types",
                        "source_type": source_type,
                        "target_type": target_type,
                    },
                )
            ]

        results = []
        for src_id, _ in sources:
            for tgt_id, _ in targets:
                result = self.check_path(
                    src_id,
                    tgt_id,
                    reason_template=(
                        f"Path from {source_type} '{{source}}' "
                        f"to {target_type} '{{target}}' via {{path}}"
                    ),
                )
                result.metadata["check"] = "cross_resource_paths"
                results.append(result)

        return results

    # ------------------------------------------------------------------
    # Aggregate runner
    # ------------------------------------------------------------------

    def detect_all(self):
        """Run every available detection check and return combined results.

        Returns:
            list[DriftResult]
        """
        results = []
        results.extend(self.detect_public_database_exposure())
        return results

    # ------------------------------------------------------------------
    # Convenience serialisation
    # ------------------------------------------------------------------

    def detect_all_as_dicts(self):
        """Run all checks and return results as plain dicts."""
        return [r.to_dict() for r in self.detect_all()]