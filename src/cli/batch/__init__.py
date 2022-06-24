import click
from .commands import parse


@click.group()
def batch() -> None:
    """Subcommands for batch depositing peer reviews from MECA archives."""
    pass


batch.add_command(parse)
