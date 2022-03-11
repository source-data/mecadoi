import click
from src.crossref import deposit as deposit_xml, generate_peer_review_deposition
from src.cli.meca.options import meca_archive, read_meca, strict_validation
from src.cli.dois.options import path_to_existing_doi_db

@click.command()
@meca_archive
@strict_validation
@path_to_existing_doi_db
def generate(meca_archive, strict_validation, path_to_existing_doi_db):
    """Generate a CrossRef deposition file for any reviews within the given MECA archive."""
    try:
        meca = read_meca(meca_archive, strict_validation)
        deposition_xml = generate_peer_review_deposition(meca, path_to_existing_doi_db)
    except ValueError as e:
        raise click.ClickException(e)

    click.echo(deposition_xml)
