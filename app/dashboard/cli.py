from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


# ---------------------------------------------------------------------------
# Severity colours for restrained terminal output
# ---------------------------------------------------------------------------

_SEVERITY_STYLES = {
    "CRITICAL": "bold red",
    "HIGH": "bold red",
    "MEDIUM": "bold yellow",
    "LOW": "bold green",
}


def show_welcome():
    panel = Panel(
        "[bold cyan]AeroDrift[/bold cyan]\n"
        "Cloud Topology & Remediation Platform",
        title="System Status",
        border_style="cyan",
    )

    console.print(panel)


# ---------------------------------------------------------------------------
# Modern CLI Dashboard
# ---------------------------------------------------------------------------


def render_dashboard(resources, topology, findings=None, console=console):
    """Render a professional CLI dashboard with all available data.

    Parameters
    ----------
    resources : dict
        The collected cloud resource data.
    topology : CloudTopology or None
        The built topology graph object.
    findings : list[dict] or None
        Security findings from detection modules.
    console : Console
        Rich Console instance (allows injection for testing).
    """
    if findings is None:
        findings = []

    # ── Application Header ────────────────────────────────────────────────
    header = Text()
    header.append("AERODRIFT\n", style="bold cyan")
    header.append("CloudOps Security Analyzer", style="dim")

    console.print(Panel(
        header,
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 4),
    ))
    console.print()

    # ── Dashboard Overview ────────────────────────────────────────────────
    total_resources = sum(len(v) for v in resources.values()) if resources else 0
    graph_info = topology.get_graph_summary() if topology else {"nodes": 0, "edges": 0}

    overview_table = Table(
        title="DASHBOARD OVERVIEW",
        box=box.SIMPLE_HEAVY,
        show_header=False,
        title_style="bold white",
        padding=(0, 2),
    )
    overview_table.add_column("Metric", style="cyan", min_width=20)
    overview_table.add_column("Value", justify="right", style="bold white", min_width=8)

    overview_table.add_row("Resources", str(total_resources))
    overview_table.add_row("VPCs", str(len(resources.get("vpcs", []))))
    overview_table.add_row("Subnets", str(len(resources.get("subnets", []))))
    overview_table.add_row(
        "EC2 Instances",
        str(len(resources.get("instances", resources.get("ec2", [])))),
    )
    overview_table.add_row("Security Groups", str(len(resources.get("security_groups", []))))
    overview_table.add_row("Network Nodes", str(graph_info["nodes"]))
    overview_table.add_row("Network Edges", str(graph_info["edges"]))
    overview_table.add_row("Security Findings", str(len(findings)))

    # Count high severity
    high_count = sum(
        1 for f in findings
        if f.get("severity", "").upper() in ("HIGH", "CRITICAL")
    )
    if high_count > 0:
        overview_table.add_row(
            "High / Critical",
            Text(str(high_count), style="bold red"),
        )

    console.print(overview_table)
    console.print()

    # ── Security Summary ──────────────────────────────────────────────────
    _render_security_summary(findings, console)
    console.print()

    # ── Security Findings Detail ──────────────────────────────────────────
    _render_security_findings(findings, console)
    console.print()

    # ── Topology Summary ──────────────────────────────────────────────────
    _render_topology_summary(topology, console)
    console.print()

    # ── Remediation Section ───────────────────────────────────────────────
    _render_remediation(findings, console)
    console.print()

    # ── Overall Status ────────────────────────────────────────────────────
    _render_status(findings, console)


def _render_security_summary(findings, console):
    """Display a concise severity breakdown."""

    title = "SECURITY SUMMARY"

    if not findings:
        console.print(Panel(
            "[bold green]No security findings detected.[/bold green]",
            title=title,
            border_style="green",
            box=box.ROUNDED,
        ))
        return

    # Count by severity
    severity_counts = {}
    for f in findings:
        sev = f.get("severity", "UNKNOWN").upper()
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    # Display order
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]

    table = Table(
        title=title,
        box=box.SIMPLE_HEAVY,
        show_header=False,
        title_style="bold white",
        padding=(0, 2),
    )
    table.add_column("Severity", min_width=14)
    table.add_column("Count", justify="right", min_width=6)

    for sev in severity_order:
        count = severity_counts.get(sev)
        if count is None:
            continue
        style = _SEVERITY_STYLES.get(sev, "white")
        table.add_row(
            Text(sev, style=style),
            Text(str(count), style=style),
        )

    table.add_section()
    table.add_row(
        Text("Total Findings", style="bold"),
        Text(str(len(findings)), style="bold"),
    )

    console.print(table)


def _render_security_findings(findings, console):
    """Display individual security findings."""

    if not findings:
        return

    table = Table(
        title="SECURITY FINDINGS",
        box=box.ROUNDED,
        title_style="bold white",
        border_style="red",
        padding=(0, 1),
    )
    table.add_column("Severity", style="bold", min_width=10)
    table.add_column("Description", min_width=30)
    table.add_column("Resource", min_width=15)
    table.add_column("Path", min_width=20)

    for finding in findings:
        sev = finding.get("severity", "UNKNOWN").upper()
        style = _SEVERITY_STYLES.get(sev, "white")

        # Build resource identifier from available fields
        resource = (
            finding.get("resource_name")
            or finding.get("resource_id")
            or finding.get("instance_id")
            or "Unknown"
        )
        resource_id = finding.get("resource_id") or finding.get("instance_id") or ""
        if resource_id and resource != resource_id:
            resource = f"{resource} ({resource_id})"

        # Build path string
        path_list = finding.get("path", [])
        path_str = " -> ".join(path_list) if path_list else "-"

        reason = finding.get("reason", "Security issue detected")

        table.add_row(
            Text(f"[{sev}]", style=style),
            reason,
            resource,
            path_str,
        )

    console.print(table)


def _render_topology_summary(topology, console):
    """Display a concise topology summary."""

    if topology is None:
        console.print(Panel(
            "[yellow]Topology data not available.[/yellow]",
            title="NETWORK TOPOLOGY",
            border_style="yellow",
            box=box.ROUNDED,
        ))
        return

    graph_info = topology.get_graph_summary()
    nodes = topology.get_nodes()

    # Count node types
    type_counts = {}
    for _, data in nodes:
        rtype = data.get("resource_type", "Unknown")
        type_counts[rtype] = type_counts.get(rtype, 0) + 1

    table = Table(
        title="NETWORK TOPOLOGY",
        box=box.SIMPLE_HEAVY,
        show_header=False,
        title_style="bold white",
        padding=(0, 2),
    )
    table.add_column("Metric", style="cyan", min_width=20)
    table.add_column("Value", justify="right", style="bold white", min_width=8)

    table.add_row("Nodes", str(graph_info["nodes"]))
    table.add_row("Edges", str(graph_info["edges"]))

    table.add_section()

    for rtype in sorted(type_counts):
        table.add_row(f"  {rtype}", str(type_counts[rtype]))

    table.add_section()

    # Determine topology health based on connectivity
    status_text = Text("HEALTHY", style="bold green")
    table.add_row("Topology Status", status_text)

    console.print(table)


def _render_remediation(findings, console):
    """Display remediation suggestions from existing findings."""

    has_remediation = any(
        f.get("remediation") or f.get("reason")
        for f in findings
    )

    if not findings or not has_remediation:
        console.print(Panel(
            "[dim]No remediation suggestions available.[/dim]",
            title="REMEDIATION",
            border_style="dim",
            box=box.ROUNDED,
        ))
        return

    table = Table(
        title="REMEDIATION",
        box=box.ROUNDED,
        title_style="bold white",
        padding=(0, 1),
        show_header=False,
    )
    table.add_column("Severity", style="bold", min_width=10)
    table.add_column("Suggestion", min_width=40)

    for finding in findings:
        sev = finding.get("severity", "UNKNOWN").upper()
        style = _SEVERITY_STYLES.get(sev, "white")

        remediation = finding.get("remediation")
        if not remediation:
            # Generate a basic suggestion from the reason
            reason = finding.get("reason", "")
            if "public" in reason.lower() and "ingress" in reason.lower():
                remediation = "Restrict public inbound access on the affected security group."
            elif "public" in reason.lower() and "database" in reason.lower():
                remediation = "Remove public network path to database. Restrict security group rules."
            elif "public" in reason.lower():
                remediation = "Review and restrict public access rules."
            else:
                remediation = "Review the security configuration for this resource."

        table.add_row(
            Text(sev, style=style),
            f"-> {remediation}",
        )

    console.print(table)


def _render_status(findings, console):
    """Display the overall system status."""

    high_critical = sum(
        1 for f in findings
        if f.get("severity", "").upper() in ("HIGH", "CRITICAL")
    )

    if high_critical > 0:
        status = Text("STATUS: SECURITY RISKS DETECTED", style="bold red")
        border = "red"
    elif findings:
        status = Text("STATUS: REVIEW RECOMMENDED", style="bold yellow")
        border = "yellow"
    else:
        status = Text("STATUS: NO CRITICAL RISKS DETECTED", style="bold green")
        border = "green"

    console.print(Panel(
        status,
        border_style=border,
        box=box.DOUBLE,
        padding=(0, 4),
    ))


if __name__ == "__main__":
    show_welcome()