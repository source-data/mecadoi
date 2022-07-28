import click
from .commands import generate, verify


@click.group()
def crossref() -> None:
    """Subcommands for interacting with the Crossref API."""
    pass


crossref.add_command(generate)
crossref.add_command(verify)
