import click

doi_db_option_names = ['-d', '--doi-db']
doi_db_option_kwargs = {
    'default': 'data/dois.sqlite3',
    'help': 'The path to the DOI database.',
}

path_to_existing_doi_db = click.option(
    'path_to_existing_doi_db', # the name of the Python parameter
    *doi_db_option_names,
    **doi_db_option_kwargs,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        allow_dash=False,
    ),
)

doi_db_path = click.option(
    'doi_db_path',
    *doi_db_option_names,
    **doi_db_option_kwargs,
    type=click.Path(),
)