import click
from .commands import generate


@click.group()
def batch() -> None:
    """Subcommands for batch depositing peer reviews from MECA archives."""
    pass


batch.add_command(generate)
