import click
from .commands import generate

@click.group()
def crossref():
    """Subcommands for interacting with the Crossref API."""
    pass

crossref.add_command(generate)