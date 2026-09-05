from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.align import Align
from rich.columns import Columns
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

# Colour per resource type for topology tree labels
_TYPE_COLORS = {
    "VPC": "bold cyan",
    "Subnet": "yellow",
    "EC2": "green",
    "SecurityGroup": "magenta",
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
# Dashboard width helpers
# ---------------------------------------------------------------------------

def _get_dashboard_width(console):
    """Return a clamped dashboard width based on terminal size."""
    w = console.width
    return max(60, min(w - 2, 100))


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
    if resources is None:
        resources = {}

    width = _get_dashboard_width(console)

    # ── 1. AERODRIFT Header ───────────────────────────────────────────────
    _render_header(console, width)

    # ── 2. SYSTEM OVERVIEW ────────────────────────────────────────────────
    _render_system_overview(resources, topology, findings, console, width)

    # ── 3. INFRASTRUCTURE + SECURITY SUMMARY (side by side) ──────────────
    _render_infra_and_security(resources, findings, console, width)

    # ── 4. CLOUD TOPOLOGY ─────────────────────────────────────────────────
    _render_topology_tree(topology, console, width)

    # ── 5. SECURITY FINDINGS ──────────────────────────────────────────────
    _render_security_findings(findings, console, width)

    # ── 6. REMEDIATION ────────────────────────────────────────────────────
    _render_remediation(findings, console, width)

    # ── 7. QUICK ACTIONS ──────────────────────────────────────────────────
    _render_quick_actions(console, width)


# ---------------------------------------------------------------------------
# 1. Header
# ---------------------------------------------------------------------------

def _render_header(console, width):
    """Compact centered header panel."""
    header = Text(justify="center")
    header.append("AERODRIFT\n", style="bold cyan")
    header.append("CloudOps Security & Topology Analyzer", style="dim")

    console.print(Panel(
        Align.center(header),
        box=box.ROUNDED,
        border_style="cyan",
        width=width,
        padding=(0, 2),
    ))


# ---------------------------------------------------------------------------
# 2. System Overview
# ---------------------------------------------------------------------------

def _render_system_overview(resources, topology, findings, console, width):
    """Compact single-row overview with key metrics."""
    total_resources = sum(len(v) for v in resources.values()) if resources else 0
    graph_info = topology.get_graph_summary() if topology else {"nodes": 0, "edges": 0}
    finding_count = len(findings)
    high_risk = sum(
        1 for f in findings
        if f.get("severity", "").upper() in ("HIGH", "CRITICAL")
    )

    # Determine status (ASCII-safe for Windows cp1252 terminals)
    if high_risk > 0:
        status_text = Text("! CRITICAL", style="bold red")
    elif finding_count > 0:
        status_text = Text("* WARN", style="bold yellow")
    else:
        status_text = Text("+ OK", style="bold green")

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold white",
        padding=(0, 1),
        show_edge=False,
        expand=False,
    )
    table.add_column("Resources", justify="center", style="cyan", min_width=9)
    table.add_column("Nodes", justify="center", style="cyan", min_width=7)
    table.add_column("Connections", justify="center", style="cyan", min_width=11)
    table.add_column("Findings", justify="center", style="cyan", min_width=8)
    table.add_column("High Risk", justify="center", style="cyan", min_width=9)
    table.add_column("Status", justify="center", min_width=10)

    high_risk_text = Text(str(high_risk), style="bold red") if high_risk > 0 else Text(str(high_risk))

    table.add_row(
        str(total_resources),
        str(graph_info["nodes"]),
        str(graph_info["edges"]),
        str(finding_count),
        high_risk_text,
        status_text,
    )

    console.print(Panel(
        table,
        title="[bold white] SYSTEM OVERVIEW [/bold white]",
        title_align="left",
        box=box.ROUNDED,
        border_style="white",
        width=width,
        padding=(0, 1),
    ))


# ---------------------------------------------------------------------------
# 3. Infrastructure + Security Summary (side by side)
# ---------------------------------------------------------------------------

def _render_infra_and_security(resources, findings, console, width):
    """Render infrastructure and security summary panels side by side."""
    half_width = (width - 3) // 2  # 3 = gap between panels

    # -- Infrastructure panel --
    infra_lines = []
    labels_values = [
        ("VPCs", len(resources.get("vpcs", []))),
        ("Subnets", len(resources.get("subnets", []))),
        ("EC2 Instances", len(resources.get("instances", resources.get("ec2", [])))),
        ("Security Groups", len(resources.get("security_groups", []))),
    ]
    inner_w = half_width - 4  # borders + padding
    for label, value in labels_values:
        val_str = str(value)
        pad = inner_w - len(label) - len(val_str)
        if pad < 1:
            pad = 1
        infra_lines.append(f"[cyan]{label}[/cyan]{' ' * pad}[bold white]{val_str}[/bold white]")

    infra_panel = Panel(
        "\n".join(infra_lines),
        title="[bold white] INFRASTRUCTURE [/bold white]",
        title_align="left",
        box=box.ROUNDED,
        border_style="white",
        width=half_width,
        padding=(0, 1),
    )

    # -- Security Summary panel --
    severity_counts = {}
    for f in findings:
        sev = f.get("severity", "UNKNOWN").upper()
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    sec_lines = []
    severity_display = [
        ("HIGH", "HIGH", "bold red"),
        ("MEDIUM", "MEDIUM", "bold yellow"),
        ("LOW", "LOW", "yellow"),
        ("SECURE", "_SECURE", "bold green"),
    ]

    for label, key, style in severity_display:
        if key == "_SECURE":
            # Count resources with no findings (informational)
            total_resources = sum(len(v) for v in resources.values()) if resources else 0
            affected_resources = len(set(
                f.get("resource_id") or f.get("instance_id") or ""
                for f in findings
            ) - {""})
            value = max(0, total_resources - affected_resources)
        else:
            # Combine CRITICAL into HIGH for display
            if key == "HIGH":
                value = severity_counts.get("HIGH", 0) + severity_counts.get("CRITICAL", 0)
            else:
                value = severity_counts.get(key, 0)
        val_str = str(value)
        pad = inner_w - len(label) - len(val_str)
        # Account for emoji width (some take 2 columns)
        pad = max(1, pad - 1)
        sec_lines.append(f"[{style}]{label}[/{style}]{' ' * pad}[bold white]{val_str}[/bold white]")

    sec_panel = Panel(
        "\n".join(sec_lines),
        title="[bold white] SECURITY SUMMARY [/bold white]",
        title_align="left",
        box=box.ROUNDED,
        border_style="white",
        width=half_width,
        padding=(0, 1),
    )

    console.print(Columns([infra_panel, sec_panel], padding=1, expand=False))


# ---------------------------------------------------------------------------
# 4. Cloud Topology (tree view)
# ---------------------------------------------------------------------------

def _topo_label(resource_type, resource_id, name):
    """Build a Rich-formatted label for topology tree nodes."""
    color = _TYPE_COLORS.get(resource_type, "white")
    label = f"[{color}]{resource_type}[/{color}]: {resource_id}"
    if name:
        label += f" ({name})"
    return label


def _topo_add_children(parent_branch, nx_graph, node_id):
    """Recursively add child nodes to the topology tree branch."""
    for child_id in nx_graph.successors(node_id):
        child_data = nx_graph.nodes.get(child_id, {})
        child_type = child_data.get("resource_type") or child_data.get("type", "Resource")
        child_name = child_data.get("name")
        child_branch = parent_branch.add(_topo_label(child_type, child_id, child_name))
        _topo_add_children(child_branch, nx_graph, child_id)


def _render_topology_tree(topology, console, width):
    """Render the cloud topology as a tree inside a bordered panel."""
    if topology is None:
        console.print(Panel(
            "[yellow]Topology data not available.[/yellow]",
            title="[bold white] CLOUD TOPOLOGY [/bold white]",
            title_align="left",
            border_style="yellow",
            box=box.ROUNDED,
            width=width,
            padding=(0, 1),
        ))
        return

    nx_graph = topology.graph if hasattr(topology, "graph") else topology

    # Build tree (without a root label — each VPC is a top-level entry)
    tree = Tree("")
    roots = [n for n in nx_graph.nodes() if nx_graph.in_degree(n) == 0]

    if not roots:
        console.print(Panel(
            "[dim]No topology nodes found.[/dim]",
            title="[bold white] CLOUD TOPOLOGY [/bold white]",
            title_align="left",
            border_style="dim",
            box=box.ROUNDED,
            width=width,
            padding=(0, 1),
        ))
        return

    for root_id in roots:
        root_data = nx_graph.nodes.get(root_id, {})
        root_type = root_data.get("resource_type") or root_data.get("type", "Resource")
        root_name = root_data.get("name")
        root_branch = tree.add(_topo_label(root_type, root_id, root_name))
        _topo_add_children(root_branch, nx_graph, root_id)

    console.print(Panel(
        tree,
        title="[bold white] CLOUD TOPOLOGY [/bold white]",
        title_align="left",
        box=box.ROUNDED,
        border_style="white",
        width=width,
        padding=(0, 1),
    ))


# ---------------------------------------------------------------------------
# 5. Security Findings
# ---------------------------------------------------------------------------

def _render_security_findings(findings, console, width):
    """Display security findings in a bordered panel."""
    if not findings:
        console.print(Panel(
            "[bold green][+] No security findings detected.[/bold green]",
            title="[bold white] SECURITY FINDINGS [/bold white]",
            title_align="left",
            box=box.ROUNDED,
            border_style="green",
            width=width,
            padding=(0, 1),
        ))
        return

    lines = []
    for finding in findings:
        sev = finding.get("severity", "UNKNOWN").upper()
        style = _SEVERITY_STYLES.get(sev, "white")

        # Build resource identifier
        resource = (
            finding.get("resource_name")
            or finding.get("resource_id")
            or finding.get("instance_id")
            or "Unknown"
        )
        resource_id = finding.get("resource_id") or finding.get("instance_id") or ""
        if resource_id and resource != resource_id:
            resource_label = f"{resource_id}"
        else:
            resource_label = resource

        reason = finding.get("reason", "Security issue detected")

        lines.append(f"[{style}][{sev}][/{style}] [bold]{resource_label}[/bold]")
        lines.append(f"  {reason}")
        lines.append("")

    # Remove trailing blank line
    if lines and lines[-1] == "":
        lines.pop()

    console.print(Panel(
        "\n".join(lines),
        title="[bold white] SECURITY FINDINGS [/bold white]",
        title_align="left",
        box=box.ROUNDED,
        border_style="red",
        width=width,
        padding=(0, 1),
    ))


# ---------------------------------------------------------------------------
# 6. Remediation
# ---------------------------------------------------------------------------

def _get_remediation_text(finding):
    """Generate a remediation suggestion from a finding."""
    remediation = finding.get("remediation")
    if remediation:
        return remediation

    reason = finding.get("reason", "")
    resource_id = finding.get("resource_id") or finding.get("instance_id") or ""
    sgs = finding.get("security_groups", [])
    sg_ref = sgs[0] if sgs else resource_id

    if "public" in reason.lower() and "ingress" in reason.lower():
        return f"Restrict public inbound access on {sg_ref}" if sg_ref else "Restrict public inbound access on the affected security group."
    elif "public" in reason.lower() and "database" in reason.lower():
        return f"Remove public network path to database. Restrict security group rules on {sg_ref}." if sg_ref else "Remove public network path to database. Restrict security group rules."
    elif "public" in reason.lower():
        return f"Review and restrict public access rules on {sg_ref}." if sg_ref else "Review and restrict public access rules."
    else:
        return "Review the security configuration for this resource."


def _render_remediation(findings, console, width):
    """Display remediation suggestions in a bordered panel."""
    has_remediation = any(
        f.get("remediation") or f.get("reason")
        for f in findings
    )

    if not findings or not has_remediation:
        console.print(Panel(
            "[dim]No remediation actions required.[/dim]",
            title="[bold white] REMEDIATION [/bold white]",
            title_align="left",
            border_style="dim",
            box=box.ROUNDED,
            width=width,
            padding=(0, 1),
        ))
        return

    lines = []
    lines.append(f"[bold yellow](!) {len(findings)} remediation action(s) recommended[/bold yellow]")
    lines.append("")

    for i, finding in enumerate(findings, 1):
        suggestion = _get_remediation_text(finding)
        lines.append(f"  {i}. {suggestion}")

    console.print(Panel(
        "\n".join(lines),
        title="[bold white] REMEDIATION [/bold white]",
        title_align="left",
        box=box.ROUNDED,
        border_style="yellow",
        width=width,
        padding=(0, 1),
    ))


# ---------------------------------------------------------------------------
# 7. Quick Actions
# ---------------------------------------------------------------------------

def _render_quick_actions(console, width):
    """Display available CLI commands as quick actions."""
    actions = (
        "[bold cyan][1][/bold cyan] Scan Infrastructure   "
        "[bold cyan][2][/bold cyan] View Findings   "
        "[bold cyan][3][/bold cyan] View Topology   "
        "[bold cyan][4][/bold cyan] Remediation   "
        "[bold cyan][Q][/bold cyan] Exit"
    )

    console.print(Panel(
        actions,
        title="[bold white] QUICK ACTIONS [/bold white]",
        title_align="left",
        box=box.ROUNDED,
        border_style="dim",
        width=width,
        padding=(0, 1),
    ))


if __name__ == "__main__":
    show_welcome()