from typing import BinaryIO, TextIO
import click
from yaml import dump
from src.cli.meca.options import meca_archive, read_meca, strict_validation
from src.crossref.api import deposit as deposit_xml
from src.crossref.peer_review import generate_peer_review_deposition
from src.crossref.verify import verify as verify_xml
from .options import verbose_output


@click.command()
@meca_archive
@strict_validation
@click.option(
    '-o', '--output',
    default='-',
    help='Write the CrossRef deposition file to this file. Defaults to stdout.',
    type=click.File('wb'),
)
def generate(meca_archive: str, strict_validation: bool, output: BinaryIO) -> None:
    """Generate a CrossRef deposition file for any reviews within the given MECA archive."""
    try:
        meca = read_meca(meca_archive, strict_validation)
        deposition_xml = generate_peer_review_deposition(meca)
    except ValueError as e:
        raise click.ClickException(str(e))

    output.write(deposition_xml)


@click.command()
@click.argument(
    'deposition-file',
    type=click.File('rb'),
)
def verify(deposition_file: BinaryIO) -> None:
    """Verify that the DOIs in the given deposition file link to existing resources."""
    try:
        result = verify_xml(deposition_file)
    except Exception as e:
        raise click.ClickException(str(e))

    click.echo(str(dump(result, canonical=False)), nl=False)


@click.command()
@click.argument(
    'deposition-file',
    type=click.File('rb'),
)
@verbose_output
@click.option(
    '-o', '--output',
    default='-',
    help='Write the response returned by the CrossRef API to this file. Defaults to stdout.',
    type=click.File('w'),
)
def deposit(deposition_file: BinaryIO, verbose: int, output: TextIO) -> None:
    """Send the given deposition XML to CrossRef."""
    try:
        response = deposit_xml(deposition_file.read(), verbose=verbose)
    except Exception as e:
        raise click.ClickException(str(e))

    output.write(response)
