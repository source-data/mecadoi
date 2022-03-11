import click
from src.crossref import deposit as deposit_xml, generate_peer_review_deposition
from src.cli.meca.options import meca_archive, read_meca, strict_validation
from src.cli.dois.options import path_to_existing_doi_db

@click.command()
@meca_archive
@strict_validation
@path_to_existing_doi_db
@click.option(
    '-o', '--output-file',
    required=True,
    help='The output file.',
    type=click.Path(),
)
def generate(meca_archive, strict_validation, output_file, path_to_existing_doi_db):
    """Generate a CrossRef deposition file for any reviews within the given MECA archive."""
    meca = read_meca(meca_archive, strict_validation)
    try:
        generate_peer_review_deposition(meca, output_file, path_to_existing_doi_db)
        click.echo(f'Deposition file written to {output_file}')
    except ValueError as e:
        raise click.ClickException(e)
