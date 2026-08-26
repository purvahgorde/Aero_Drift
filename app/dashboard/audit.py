from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_drift_findings(
    findings: list[dict],
    console: Console = console,
) -> None:
    """Display detected security drift findings."""

    if not findings:
        console.print(
            Panel(
                "[bold green]No security drift detected.[/bold green]",
                title="AeroDrift Security Audit",
                border_style="green",
            )
        )
        return

    table = Table(
        title="AeroDrift Security Drift",
        border_style="red",
    )

    table.add_column("Severity", style="bold red")
    table.add_column("Resource")
    table.add_column("Security Group")
    table.add_column("Reason", no_wrap=True)
    table.add_column("Network Path")

    for finding in findings:
        path = " → ".join(finding.get("path", []))
        security_groups = ", ".join(finding.get("security_groups", []))

        table.add_row(
            finding.get("severity", "UNKNOWN"),
            f"{finding.get('resource_name', 'Unknown')} "
            f"({finding.get('resource_id', '')})",
            security_groups,
            finding.get("reason", ""),
            path,
        )

    console.print(table)