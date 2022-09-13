import click
from .commands import deposit, ls, parse, prune


@click.group()
def batch() -> None:
    """Subcommands for batch depositing peer reviews from MECA archives."""
    pass


batch.add_command(deposit)
batch.add_command(ls)
batch.add_command(parse)
batch.add_command(prune)
