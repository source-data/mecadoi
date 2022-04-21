import click
from src.meca import MECArchive

meca_archive = click.argument(
    'meca_archive',
    type=click.File(mode='rb'),
)


def read_meca(meca_archive, strict_validation):
    try:
        return MECArchive(meca_archive, strict_validation=strict_validation)
    except ValueError as e:
        raise click.ClickException(e)


strict_validation = click.option(
    '--strict-validation/--no-strict-validation',
    default=False,
    help='Should the MECA archive be strictly validated.',
)
