import click

doi_db_path = click.option(
    'doi_db_path',
    '-d', '--doi-db',
    default='data/dois.sqlite3',
    help='The path to the DOI database.',
    type=click.Path(),
)
