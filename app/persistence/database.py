"""SQLite persistence layer for AeroDrift.

Provides lightweight local storage for scan history, resource states,
security findings, and remediation results.  Uses Python's built-in
``sqlite3`` module — no external dependencies required.

Usage::

    from app.persistence.database import AeroDriftDB

    db = AeroDriftDB()                       # uses default data/aerodrift.db
    scan_id = db.create_scan("completed")
    db.save_resources(scan_id, resources)
    db.save_findings(scan_id, findings)
    db.close()
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Default database path
# ---------------------------------------------------------------------------

def _default_db_path():
    """Resolve the default database path: ``<project_root>/data/aerodrift.db``."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(app_dir))
    return os.path.join(project_root, "data", "aerodrift.db")


# ---------------------------------------------------------------------------
# Database manager
# ---------------------------------------------------------------------------

class AeroDriftDB:
    """Lightweight SQLite database manager for AeroDrift scan persistence.

    Parameters
    ----------
    db_path : str or None
        Path to the SQLite database file.  When *None*, defaults to
        ``data/aerodrift.db`` relative to the project root.
    """

    def __init__(self, db_path=None):
        self.db_path = db_path or _default_db_path()

        # Ensure the parent directory exists.
        parent = os.path.dirname(self.db_path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)

        try:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent read performance.
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._initialize_tables()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to open database at {self.db_path}: {exc}") from exc

    # ------------------------------------------------------------------
    # Schema / initialisation
    # ------------------------------------------------------------------

    def _initialize_tables(self):
        """Create tables if they do not already exist (idempotent)."""
        with self._conn:
            self._conn.executescript(_SCHEMA_SQL)

    # ------------------------------------------------------------------
    # Scan history
    # ------------------------------------------------------------------

    def create_scan(self, status="completed"):
        """Create a new scan record and return its ``scan_id``.

        Parameters
        ----------
        status : str
            Human-readable status such as ``"completed"`` or ``"failed"``.

        Returns
        -------
        str
            UUID scan identifier.
        """
        scan_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO scan_history (scan_id, timestamp, status) VALUES (?, ?, ?)",
                    (scan_id, timestamp, status),
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to create scan: {exc}") from exc
        return scan_id

    def get_latest_scan(self):
        """Return the most recent scan row, or ``None``."""
        try:
            row = self._conn.execute(
                "SELECT * FROM scan_history ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to retrieve latest scan: {exc}") from exc

    def get_previous_scan(self):
        """Return the second-most-recent scan row, or ``None``."""
        try:
            rows = self._conn.execute(
                "SELECT * FROM scan_history ORDER BY timestamp DESC LIMIT 2"
            ).fetchall()
            if len(rows) < 2:
                return None
            return dict(rows[1])
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to retrieve previous scan: {exc}") from exc

    def get_scan_by_id(self, scan_id):
        """Return a scan row by its ``scan_id``, or ``None``."""
        try:
            row = self._conn.execute(
                "SELECT * FROM scan_history WHERE scan_id = ?", (scan_id,)
            ).fetchone()
            return dict(row) if row else None
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to retrieve scan {scan_id}: {exc}") from exc

    def get_all_scans(self):
        """Return all scans ordered by timestamp descending."""
        try:
            rows = self._conn.execute(
                "SELECT * FROM scan_history ORDER BY timestamp DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to retrieve scans: {exc}") from exc

    # ------------------------------------------------------------------
    # Resource state persistence
    # ------------------------------------------------------------------

    def save_resources(self, scan_id, resources):
        """Persist cloud resource state for a given scan.

        Parameters
        ----------
        scan_id : str
            The scan to associate with.
        resources : dict
            The standard AeroDrift resource dict with keys like
            ``vpcs``, ``subnets``, ``instances``, ``security_groups``.
        """
        try:
            with self._conn:
                for resource_type, items in resources.items():
                    for item in items:
                        resource_id = item.get("id", "")
                        resource_name = (
                            item.get("name")
                            or item.get("GroupName")
                            or ""
                        )
                        # Serialize the full item dict for lossless storage.
                        state_json = json.dumps(item, default=str)

                        self._conn.execute(
                            """INSERT INTO resources
                               (scan_id, resource_id, resource_type,
                                resource_name, resource_state)
                               VALUES (?, ?, ?, ?, ?)""",
                            (scan_id, resource_id, resource_type,
                             resource_name, state_json),
                        )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to save resources for scan {scan_id}: {exc}") from exc

    def get_resources_for_scan(self, scan_id):
        """Return all resource rows for a given scan.

        Returns
        -------
        list[dict]
            Each dict contains ``resource_id``, ``resource_type``,
            ``resource_name``, and ``resource_state`` (JSON string).
        """
        try:
            rows = self._conn.execute(
                "SELECT * FROM resources WHERE scan_id = ? ORDER BY resource_type, resource_id",
                (scan_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to retrieve resources for scan {scan_id}: {exc}") from exc

    # ------------------------------------------------------------------
    # Security findings persistence
    # ------------------------------------------------------------------

    def save_findings(self, scan_id, findings):
        """Persist security findings for a given scan.

        Parameters
        ----------
        scan_id : str
            The scan to associate with.
        findings : list[dict]
            Security finding dicts as produced by detection modules.
        """
        if not findings:
            return
        try:
            with self._conn:
                for finding in findings:
                    resource_id = (
                        finding.get("resource_id")
                        or finding.get("instance_id")
                        or ""
                    )
                    severity = finding.get("severity", "UNKNOWN")
                    finding_type = finding.get("finding_type", "security")
                    title = finding.get("reason", "Security issue detected")
                    description_json = json.dumps(finding, default=str)

                    self._conn.execute(
                        """INSERT INTO security_findings
                           (scan_id, resource_id, severity,
                            finding_type, title, description)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (scan_id, resource_id, severity,
                         finding_type, title, description_json),
                    )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to save findings for scan {scan_id}: {exc}") from exc

    def get_findings_for_scan(self, scan_id):
        """Return all security finding rows for a given scan."""
        try:
            rows = self._conn.execute(
                "SELECT * FROM security_findings WHERE scan_id = ?",
                (scan_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to retrieve findings for scan {scan_id}: {exc}") from exc

    # ------------------------------------------------------------------
    # Remediation results persistence
    # ------------------------------------------------------------------

    def save_remediation_results(self, scan_id, remediation_results):
        """Persist remediation results for a given scan.

        Parameters
        ----------
        scan_id : str
            The scan to associate with.
        remediation_results : list[dict]
            Each dict should contain ``resource_id``, ``action``, and ``status``.
        """
        if not remediation_results:
            return
        try:
            with self._conn:
                for result in remediation_results:
                    resource_id = result.get("resource_id", "")
                    action = result.get("action", "")
                    status = result.get("status", "PENDING")

                    self._conn.execute(
                        """INSERT INTO remediation_results
                           (scan_id, resource_id, action, status)
                           VALUES (?, ?, ?, ?)""",
                        (scan_id, resource_id, action, status),
                    )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to save remediation results for scan {scan_id}: {exc}") from exc

    def get_remediation_for_scan(self, scan_id):
        """Return all remediation result rows for a given scan."""
        try:
            rows = self._conn.execute(
                "SELECT * FROM remediation_results WHERE scan_id = ?",
                (scan_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to retrieve remediation results for scan {scan_id}: {exc}") from exc

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class DatabaseError(Exception):
    """Raised when a database operation fails."""
    pass


# ---------------------------------------------------------------------------
# Schema SQL (idempotent)
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scan_history (
    scan_id    TEXT PRIMARY KEY,
    timestamp  TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'completed'
);

CREATE TABLE IF NOT EXISTS resources (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id        TEXT NOT NULL,
    resource_id    TEXT NOT NULL,
    resource_type  TEXT NOT NULL,
    resource_name  TEXT NOT NULL DEFAULT '',
    resource_state TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (scan_id) REFERENCES scan_history(scan_id)
);

CREATE INDEX IF NOT EXISTS idx_resources_scan_id
    ON resources(scan_id);

CREATE INDEX IF NOT EXISTS idx_resources_resource_id
    ON resources(resource_id);

CREATE TABLE IF NOT EXISTS security_findings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id      TEXT NOT NULL,
    resource_id  TEXT NOT NULL DEFAULT '',
    severity     TEXT NOT NULL DEFAULT 'UNKNOWN',
    finding_type TEXT NOT NULL DEFAULT 'security',
    title        TEXT NOT NULL DEFAULT '',
    description  TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (scan_id) REFERENCES scan_history(scan_id)
);

CREATE INDEX IF NOT EXISTS idx_findings_scan_id
    ON security_findings(scan_id);

CREATE TABLE IF NOT EXISTS remediation_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id     TEXT NOT NULL,
    resource_id TEXT NOT NULL DEFAULT '',
    action      TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'PENDING',
    FOREIGN KEY (scan_id) REFERENCES scan_history(scan_id)
);

CREATE INDEX IF NOT EXISTS idx_remediation_scan_id
    ON remediation_results(scan_id);
"""
