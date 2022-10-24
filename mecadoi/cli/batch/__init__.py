import click
from .commands import deposit, ls, parse, prune


@click.group()
def batch() -> None:
    """
    Create DOIs for peer reviews and author replies in MECA archives.

    All actions taken during these commands are recorded in the MECADOI database.
    Its location can be set through the `DB_URL` parameter in the `.env` file.
    """
    pass


batch.add_command(deposit)
batch.add_command(ls)
batch.add_command(parse)
batch.add_command(prune)
