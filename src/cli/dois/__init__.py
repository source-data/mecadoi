import click
from .commands import info, add


@click.group()
def dois() -> None:
    """Subcommands for interacting with the DOI database."""
    pass


dois.add_command(info)
dois.add_command(add)
