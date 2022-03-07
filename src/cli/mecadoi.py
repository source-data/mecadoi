import click
from zipfile import ZipFile

from src.crossref.dois import DoiDatabase
from src.meca import MECArchive

meca_archive = click.option(
    '-m', '--meca-archive',
    required=True,
    help='The MECA archive to read.',
    type=click.File('rb'),
)
strict_validation = click.option(
    '--strict-validation/--no-strict-validation',
    default=False,
    help='Should the MECA archive be strictly validated.',
)
doi_db = click.option(
    '-d', '--doi-db',
    default='data/dois.sqlite3',
    help='The database file holding the DOIs to be assigned to the peer reviews.',
    type=click.File('rb'),
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
@doi_db
@click.option(
    '-o', '--output-file',
    required=True,
    help='The output file.',
    type=click.Path(),
)
def generate(meca_archive, strict_validation, output_file, doi_db):
    """Generate a CrossRef deposition file for any reviews within the given MECA archive."""
    meca = read_meca(meca_archive, strict_validation)
    try:
        generate_peer_review_deposition(meca, output_file)
        click.echo(f'Deposition file written to {output_file}')
    except ValueError as e:
        raise click.ClickException(e)


@cli.group()
@click.pass_context
@click.option(
    '-d', '--doi-db',
    default='data/dois.sqlite3',
    help='The path to the DOI database.',
    type=click.Path(),
)
def dois(ctx, doi_db):
    """Subcommands for interacting with the DOI database."""
    ctx.ensure_object(dict)
    ctx.obj['doi_db_path'] = click.format_filename(doi_db)
    ctx.obj['doi_db'] = DoiDatabase(doi_db)

@dois.command('fill')
@click.pass_context
@click.option(
    '-i', '--input',
    default='-',
    help='The input file containing the DOIs to be added to the database.',
    type=click.Path(),
)
def fill_doi_db(ctx, input):
    """Add the DOIs from the given input file to the given DOI database. If not input file is given, stdin is read."""
    try:
        with click.open_file(input, 'r') as f:
            dois = f.read().splitlines()

        doi_db = ctx.obj['doi_db']
        doi_db.initialize()
        doi_db.insert_dois(dois)

        doi_db_path = ctx.obj["doi_db_path"]
        num_added_dois = len(dois)
        click.echo(f'Added {num_added_dois} {"DOI" if num_added_dois == 1 else "DOIs"} to "{doi_db_path}"')
    except Exception as e:
        raise click.ClickException(e)

@dois.command('info')
@click.pass_context
def doi_db_info(ctx):
    """Get info from the given DOI database: how many unused DOIs are there and how many in total."""
    try:
        doi_db = ctx.obj['doi_db']
        num_free_dois = doi_db.get_num_free_dois()
        num_total_dois = doi_db.get_num_total_dois()
    except Exception as e:
        raise click.ClickException(e)

    doi_db_path = ctx.obj["doi_db_path"]
    click.echo(f'DOI database "{doi_db_path}" has {num_free_dois} unused {"DOI" if num_free_dois == 1 else "DOIs"} and {num_total_dois} in total.')

if __name__ == '__main__':
    cli()