from io import BufferedReader
import click
from src.crossref import deposit as deposit_xml, generate_peer_review_deposition
from src.cli.meca.options import meca_archive, read_meca, strict_validation
from src.cli.dois.options import path_to_existing_doi_db

@click.command()
@meca_archive
@strict_validation
@path_to_existing_doi_db
@click.option(
    '-o', '--output',
    default='-',
    help='Write the CrossRef deposition file to this file. Defaults to stdout.',
    type=click.File('wb'),
)
def generate(meca_archive, strict_validation, path_to_existing_doi_db, output):
    """Generate a CrossRef deposition file for any reviews within the given MECA archive."""
    try:
        meca = read_meca(meca_archive, strict_validation)
        deposition_xml = generate_peer_review_deposition(meca, path_to_existing_doi_db)
    except ValueError as e:
        raise click.ClickException(e)

    output.write(deposition_xml)

@click.command()
@click.argument(
    'deposition-file',
    type=click.File('rb'),
)
@click.option(
    '-u', '--crossref-username',
    envvar='CROSSREF_USERNAME',
)
@click.option(
    '-p', '--crossref-password',
    envvar='CROSSREF_PASSWORD',
)
@click.option(
    '-v', '--verbose',
    count=True,
)
@click.option(
    '--sandbox/--no-sandbox',
    default=True,
    help='Should the CrossRef sandbox be used for deposition.',
)
@click.option(
    '-o', '--output',
    default='-',
    help='Write the response returned by the CrossRef API to this file. Defaults to stdout.',
    type=click.File('w'),
)
def deposit(deposition_file: BufferedReader, crossref_username: str, crossref_password: str, verbose: int, sandbox: bool, output):
    """Send the given deposition XML to CrossRef."""
    try:
        response = deposit_xml(deposition_file.read(), crossref_username, crossref_password, verbose=verbose, sandbox=sandbox)
    except Exception as e:
        raise click.ClickException(e)

    output.write(response)
