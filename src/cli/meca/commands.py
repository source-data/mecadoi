import click
from yaml import dump
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
                    'date_completed': review.date_completed.strftime('%Y-%m-%d'),
                    'contributors': review.contributors,
                }
                for review in revision_round.reviews
            }
            for revision_round in meca.revision_rounds
        }
        click.echo(dump(revision_rounds), nl=False)
