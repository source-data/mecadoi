import click
from .options import meca_archive, read_meca, strict_validation

@click.command()
@meca_archive
@strict_validation
def info(meca_archive, strict_validation):
    """Show information about the given MECA archive."""
    meca = read_meca(meca_archive, strict_validation)
    click.echo(meca)
