from io import BufferedReader
import click
from src.cli.meca.options import meca_archive, read_meca, strict_validation
from src.crossref import deposit as deposit_xml, generate_peer_review_deposition
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
def generate(meca_archive, strict_validation, output):
    """Generate a CrossRef deposition file for any reviews within the given MECA archive."""
    try:
        meca = read_meca(meca_archive, strict_validation)
        deposition_xml = generate_peer_review_deposition(meca)
    except ValueError as e:
        raise click.ClickException(e)

    output.write(deposition_xml)


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
def deposit(deposition_file: BufferedReader, verbose: int, output):
    """Send the given deposition XML to CrossRef."""
    try:
        response = deposit_xml(deposition_file.read(), verbose=verbose)
    except Exception as e:
        raise click.ClickException(e)

    output.write(response)
