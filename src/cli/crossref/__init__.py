import click
from .commands import deposit, generate


@click.group()
def crossref() -> None:
    """Subcommands for interacting with the Crossref API."""
    pass


crossref.add_command(deposit)
crossref.add_command(generate)
