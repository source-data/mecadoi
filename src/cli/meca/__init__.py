import click
from .commands import info

@click.group()
def meca():
    """Interact with a MECA archive."""
    pass

meca.add_command(info)