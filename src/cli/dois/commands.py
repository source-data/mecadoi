from typing import TextIO
import click
from src.crossref.dois import DoiDatabase
from .options import doi_db_path


@click.command()
@doi_db_path
@click.argument(
    'input',
    type=click.File(mode='r'),
)
def add(doi_db_path: str, input: TextIO) -> None:
    """
    Add the DOIs from the given input file to the given DOI database.

    Each non-empty line of the input is treated as a DOI and attempted to be added to the database.
    If - is passed as input file the DOIs are read from stdin.
    """
    try:
        dois = [row for row in input.read().splitlines() if row]

        doi_db = DoiDatabase(doi_db_path)
        doi_db.initialize()
        doi_db.insert_dois(dois)

        num_added_dois = len(dois)
        click.echo(f'Added {num_added_dois} {"DOI" if num_added_dois == 1 else "DOIs"} to "{doi_db.db_file}"')
    except Exception as e:
        raise click.ClickException(str(e))


@click.command()
def info() -> None:
    """Get info from the DOI database: how many unused DOIs are there and how many in total."""
    try:
        doi_db = DoiDatabase()
        num_free_dois = doi_db.get_num_free_dois()
        num_total_dois = doi_db.get_num_total_dois()
    except Exception as e:
        raise click.ClickException(str(e))

    click.echo(f"""{doi_db.db_file}:
  num-total-dois: {num_total_dois}
  num-unused-dois: {num_free_dois}""")
