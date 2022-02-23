import click
import zipfile

from src.meca import MECArchive

@click.command()
@click.option(
    '--meca-archive',
    required=True,
    help='The MECA archive to read.',
    type=click.File('rb')
)
@click.option(
    '--strict-validation/--no-strict-validation',
    default=False,
    help='Should the MECA archive be strictly validated.'
)
def meca_info(meca_archive, strict_validation):
    """Show information about the given MECA archive."""
    with zipfile.ZipFile(meca_archive, 'r') as archive:
        meca = MECArchive(archive, strict_validation=strict_validation)
        print(meca)

if __name__ == '__main__':
    meca_info()