import click

meca_archive = click.argument(
    'meca_archive',
    type=click.File(mode='rb'),
)
