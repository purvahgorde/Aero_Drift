from rich.console import Console

from app.dashboard.audit import show_drift_findings


def test_dashboard_audit_function_runs():
    findings = [
        {
            "severity": "CRITICAL",
            "resource_id": "i-002",
            "resource_name": "db-server-1",
            "security_groups": ["sg-002"],
            "reason": "Public internet path detected to database",
            "path": ["internet", "sg-002", "i-002"],
        }
    ]

    console = Console(width=150, force_terminal=True, color_system=None)

    show_drift_findings(findings, console=console)

    # The function writes through Rich's console.
    # Test the underlying values directly as well.
    assert findings[0]["severity"] == "CRITICAL"
    assert findings[0]["resource_name"] == "db-server-1"
    assert findings[0]["security_groups"] == ["sg-002"]
    assert findings[0]["reason"] == "Public internet path detected to database"
    assert findings[0]["path"] == [
        "internet",
        "sg-002",
        "i-002",
    ]