from rich.console import Console
from rich.table import Table

console = Console()


def show_summary(state: dict) -> None:
    """Display a summary of discovered cloud resources."""

    table = Table(title="AeroDrift Infrastructure Summary")

    table.add_column("Resource", style="cyan")
    table.add_column("Count", justify="right", style="green")

    table.add_row("VPCs", str(len(state.get("vpcs", []))))
    table.add_row("Subnets", str(len(state.get("subnets", []))))
    table.add_row("EC2 Instances", str(len(state.get("instances", state.get("ec2", [])))))
    table.add_row("Security Groups", str(len(state.get("security_groups", []))))

    console.print(table)


if __name__ == "__main__":
    mock_state = {
        "vpcs": [
            {"id": "vpc-001"}
        ],
        "subnets": [
            {"id": "subnet-001"},
            {"id": "subnet-002"}
        ],
        "instances": [
            {"id": "i-001"},
            {"id": "i-002"}
        ],
        "security_groups": [
            {"id": "sg-001"}
        ]
    }

    show_summary(mock_state)