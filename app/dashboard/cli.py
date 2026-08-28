from rich.console import Console
from rich.panel import Panel

console = Console()


def show_welcome():
    panel = Panel(
        "[bold cyan]AeroDrift[/bold cyan]\n"
        "Cloud Topology & Remediation Platform",
        title="System Status",
        border_style="cyan",
    )

    console.print(panel)


if __name__ == "__main__":
    show_welcome()