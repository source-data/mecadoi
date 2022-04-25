from typing import Dict
import click
from time import gmtime, strptime, struct_time
import yaml

from src.meca.xml.review_group import Review
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

    def assigned_date(meca_review: Review) -> struct_time:
        if not meca_review.history:
            return gmtime(0)  # return the lowest possible value for reviews with unknown history
        date = meca.get_el_with_attr(meca_review.history.date, 'date_type', 'assigned')
        return strptime(f'{date.year} {date.month} {date.day}', '%Y %m %d')

    revision_rounds: Dict[str, Dict[str, Dict[str, str]]] = {}
    if meca.reviews:
        for revision_round in meca.reviews.version:
            reviews = {}
            for running_number, meca_review in enumerate(sorted(revision_round.review, key=assigned_date), start=1):
                date_completed = (
                    meca.get_el_with_attr(meca_review.history.date, 'date_type', 'completed')
                    if meca_review.history
                    else 'Unknown'
                )
                review_info = {
                    'date_completed': f'{date_completed.year}-{date_completed.month}-{date_completed.day}',
                    'contributors': ', '.join([
                        f'{contrib.name.surname}, {contrib.name.given_names}'
                        for contrib in meca_review.contrib_group.contrib
                        if contrib.name
                    ]) if meca_review.contrib_group else 'Unknown',
                }
                reviews[f'Review {running_number}'] = review_info

            revision_rounds[f'Revision round {revision_round.revision}'] = reviews
        click.echo(yaml.dump(revision_rounds))
