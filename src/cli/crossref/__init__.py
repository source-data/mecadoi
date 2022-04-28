import click
from .commands import deposit, generate, verify


@click.group()
def crossref() -> None:
    """Subcommands for interacting with the Crossref API."""
    pass


crossref.add_command(deposit)
crossref.add_command(generate)
crossref.add_command(verify)
