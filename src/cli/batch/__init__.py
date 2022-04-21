import click
from .commands import deposit


@click.group()
def batch():
    """Subcommands for batch depositing peer reviews from MECA archives."""
    pass


batch.add_command(deposit)
