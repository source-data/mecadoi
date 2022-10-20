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
@click.option(
    "--preprint-doi",
    default=None,
    help="Use this preprint DOI instead of the one found in the MECA archive.",
)
def generate(
    meca_archive: str, output: TextIO, preprint_doi: Optional[str] = None
) -> None:
    """
    Generate a CrossRef deposition file for all reviews and author replies in a MECA archive.

    This command parses the file at `MECA_ARCHIVE` and generates a Crossref deposition file for
    every peer review and author reply in the MECA archive. This deposition file can be sent to the
    Crossref API or web interface to create DOIs for these reviews and author replies.

    The DOIs to be assigned to the reviews and replies are randomly generated and not checked for
    uniqueness.
    Information such as the registrant and depositor name are taken from the `.env` file.

    This command is useful for debugging and inspection of CrossRef deposition file. It also can be
    used for manual deposition of peer review DOIs for a single MECA archive.
    """
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
    """
    Verify that the DOIs in a deposition file link to existing resources.

    Each review in the given deposition file indicates which article it reviews.
    This command queries the Early Evidence Base (EEB) API for all articles under review in the
    given deposition file. For each article, the command checks whether the reviews and responses
    available from the EEB API exactly match the reviews and responses in the deposition file. It
    also checks whether the EEB API already has DOIs for at least one of these reviews.

    As an example, if the deposition file has 3 reviews and 1 author reply belonging to article
    10.1234/5678, this command returns an error:

    \b
    - If EEB doesn't have exactly 3 reviews and 1 author reply for this article.
    - If one of these reviews or the reply already has a DOI on EEB.
    """
    try:
        result = verify_xml(deposition_file.read())
    except Exception as e:
        raise click.ClickException(str(e))

    click.echo(str(dump(result, canonical=False)), nl=False)
