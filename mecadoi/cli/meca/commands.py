from typing import List, Optional
import click
from yaml import dump

from mecadoi.meca import parse_meca_archive, Review
from mecadoi.model import Author

from .options import meca_archive


@click.command()
@meca_archive
def info(meca_archive: str) -> None:
    """
    Show basic information about the manuscript in a MECA archive.

    Parses the file at `MECA_ARCHIVE` and prints the authors, journal, title, any DOIs, and a
    summary of the peer review process of the manuscript to stdout.
    """
    manuscript = parse_meca_archive(meca_archive)
    output = {
        "title": truncate(manuscript.title),
        "doi": manuscript.doi,
        "authors": get_contributors(manuscript.authors),
    }
    if manuscript.preprint_doi:
        output["preprint_doi"] = manuscript.preprint_doi
    if manuscript.journal:
        output["journal"] = manuscript.journal
    if manuscript.review_process:
        num_revision_rounds = len(manuscript.review_process)
        num_total_reviews = sum(
            [
                len(revision_round.reviews)
                for revision_round in manuscript.review_process
            ]
        )
        num_author_replies = sum(
            [
                1 if revision_round.author_reply else 0
                for revision_round in manuscript.review_process
            ]
        )
        output["review_process"] = (
            f'{num_revision_rounds} revision round{"s" if num_revision_rounds != 1 else ""},'
            + f' {num_total_reviews} review{"s" if num_total_reviews != 1 else ""},'
            + f' {num_author_replies} author repl{"ies" if num_author_replies != 1 else "y"}'
        )
    click.echo(dump(output, width=120), nl=False)


@click.command()
@meca_archive
def reviews(meca_archive: str) -> None:
    """
    Show information about the review process of the manuscript in a MECA archive.

    Parses the file at `MECA_ARCHIVE` and prints the authors, date, and a summary of all reviews
    and author replies of the manuscript to stdout.
    """
    manuscript = parse_meca_archive(meca_archive)

    if manuscript.review_process:
        revision_rounds_info = {}
        for revision_round in manuscript.review_process:
            revision_round_info = {
                f"Review {review.running_number}": {
                    "contributors": get_contributors(review.authors),
                    "summary": (
                        get_summary("Evidence", review)
                        or get_summary("Significance", review)
                        or get_summary("", review)
                        or None
                    ),
                }
                for review in revision_round.reviews
            }
            if revision_round.author_reply:
                revision_round_info["Author Reply"] = {
                    "contributors": get_contributors(
                        revision_round.author_reply.authors
                    ),
                }

            revision_rounds_info[
                f"Revision round {revision_round.revision_id}"
            ] = revision_round_info
        click.echo(dump(revision_rounds_info, width=150), nl=False)


def get_contributors(contributors: Optional[List[Author]]) -> str:
    if not contributors:
        return "Anonymous"

    return truncate(
        ", ".join(
            [
                f"{contributor.surname}, {contributor.given_name}"
                for contributor in contributors
            ]
        )
    )


def get_summary(type: str, review: Review) -> Optional[str]:
    text = None
    for question_title, answer in review.text.items():
        if type in question_title:
            text = answer
    if text is None:
        return None

    # Normalize the text:
    text = text.strip()  # remove trailing whitespace
    text = text.replace("\r", " ").replace("\n", " ")  # remove linebreaks
    text = " ".join(
        text.split()
    )  # remove runs of multiple whitespaces: https://stackoverflow.com/a/2077944
    return truncate(text)  # cut down length if necessary


def truncate(text: str, max_length: int = 100, ellipsis: str = "...") -> str:
    if len(text) > max_length:  # cut down length if necessary
        return text[: max_length - len(ellipsis)] + ellipsis
    return text
