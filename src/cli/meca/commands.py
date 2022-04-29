from typing import Optional
import click
from yaml import dump

from src.meca.archive import ReviewInfo
from .options import meca_archive, read_meca, strict_validation


@click.command()
@meca_archive
@strict_validation
def info(meca_archive: str, strict_validation: bool) -> None:
    """Show information about the given MECA archive."""
    meca = read_meca(meca_archive, strict_validation)
    click.echo(meca)


@click.command()
@meca_archive
@strict_validation
def reviews(meca_archive: str, strict_validation: bool) -> None:
    """Show information about the reviews in the given MECA archive."""
    meca = read_meca(meca_archive, strict_validation)

    if meca.revision_rounds:
        revision_rounds = {
            f'Revision round {revision_round.revision}': {
                f'Review {review.running_number}': {
                    'date_assigned': review.date_assigned.strftime('%Y-%m-%d'),
                    'date_completed': review.date_completed.strftime('%Y-%m-%d'),
                    'contributors': review.contributors,
                    'summary': (
                        get_summary('Evidence', review)
                        or get_summary('Significance', review)
                        or get_summary('', review)
                        or None
                    ),
                }
                for review in revision_round.reviews
            }
            for revision_round in meca.revision_rounds
        }
        click.echo(dump(revision_rounds, width=150), nl=False)


def get_summary(type: str, review: ReviewInfo) -> Optional[str]:
    text = None
    for question_title, answer in review.text.items():
        if type in question_title:
            text = answer
    if text is None:
        return None

    # Normalize the text:
    text = text.strip()  # remove trailing whitespace
    text = text.replace('\r', ' ').replace('\n', ' ')  # remove linebreaks
    text = ' '.join(text.split())  # remove runs of multiple whitespaces: https://stackoverflow.com/a/2077944
    if len(text) > 100:  # cut down length if necessary
        text = text[:97] + '...'
    return text

