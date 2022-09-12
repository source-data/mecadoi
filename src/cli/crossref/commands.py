from datetime import datetime
from typing import Optional, TextIO
import click
from yaml import dump
from src.article import from_meca_manuscript
from src.cli.meca.options import meca_archive
from src.crossref.peer_review import generate_peer_review_deposition
from src.crossref.verify import verify as verify_xml
from src.dois import get_random_doi
from src.meca import parse_meca_archive


@click.command()
@meca_archive
@click.option(
    "-o",
    "--output",
    default="-",
    help="Write the CrossRef deposition file to this file. Defaults to stdout.",
    type=click.File("w"),
)
@click.option("--preprint-doi", default=None)
def generate(
    meca_archive: str, output: TextIO, preprint_doi: Optional[str] = None
) -> None:
    """Generate a CrossRef deposition file for any reviews within the given MECA archive."""
    try:
        manuscript = parse_meca_archive(meca_archive)
        article = from_meca_manuscript(
            manuscript,
            datetime.now(),
            lambda _: get_random_doi(),
            preprint_doi=preprint_doi,
        )
        deposition_xml = generate_peer_review_deposition([article])
    except ValueError as e:
        raise click.ClickException(str(e))

    output.write(deposition_xml)


@click.command()
@click.argument(
    "deposition-file",
    type=click.File("r"),
)
def verify(deposition_file: TextIO) -> None:
    """Verify that the DOIs in the given deposition file link to existing resources."""
    try:
        result = verify_xml(deposition_file.read())
    except Exception as e:
        raise click.ClickException(str(e))

    click.echo(str(dump(result, canonical=False)), nl=False)
