import click
from .commands import info, reviews


@click.group()
def meca() -> None:
    """Interact with a MECA archive."""
    pass


meca.add_command(info)
meca.add_command(reviews)
