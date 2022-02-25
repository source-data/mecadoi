import click
from zipfile import ZipFile

from src.crossref import generate_peer_review_deposition
from src.meca import MECArchive

meca_archive = click.option(
    '-m', '--meca-archive',
    required=True,
    help='The MECA archive to read.',
    type=click.File('rb')
)
strict_validation = click.option(
    '--strict-validation/--no-strict-validation',
    default=False,
    help='Should the MECA archive be strictly validated.'
)

def read_meca(meca_archive, strict_validation):
    with ZipFile(meca_archive, 'r') as archive:
        try:
            return MECArchive(archive, strict_validation=strict_validation)
        except ValueError as e:
            raise click.ClickException(e)

@click.group()
def cli():
    pass

@cli.command()
@meca_archive
@strict_validation
def info(meca_archive, strict_validation):
    """Show information about the given MECA archive."""
    meca = read_meca(meca_archive, strict_validation)
    click.echo(meca)

@cli.command()
@meca_archive
@strict_validation
@click.option(
    '-o', '--output-file',
    required=True,
    help='The output file.',
    type=click.Path()
)
def generate(meca_archive, strict_validation, output_file):
    """Generate a CrossRef deposition file for any reviews within the given MECA archive."""
    meca = read_meca(meca_archive, strict_validation)
    try:
        generate_peer_review_deposition(meca, output_file)
        click.echo(f'Deposition file written to {output_file}')
    except ValueError as e:
        raise click.ClickException(e)

if __name__ == '__main__':
    cli()