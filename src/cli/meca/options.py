import click

meca_archive = click.argument(
    'meca_archive',
    type=click.File(mode='rb'),
)

strict_validation = click.option(
    '--strict-validation/--no-strict-validation',
    default=False,
    help='Should the MECA archive be strictly validated.',
)
