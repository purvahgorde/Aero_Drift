from io import StringIO
from rich.console import Console

from app.dashboard.cli import render_dashboard


class CLIDashboard:
    

    def __init__(self, resources=None, findings=None, graph=None):
        self.resources = resources
        self.findings = findings
        self.graph = graph

    def display(self):
        """Render the dashboard and return the output as a string."""
        buf = StringIO()
        capture_console = Console(
            file=buf,
            width=100,
            force_terminal=True,
            color_system=None,
        )

        resources = self.resources if self.resources is not None else {}
        findings = self.findings if self.findings is not None else []
        topology = self.graph

        render_dashboard(
            resources=resources,
            topology=topology,
            findings=findings,
            console=capture_console,
        )

        return buf.getvalue()
