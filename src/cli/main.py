import click
from .batch import batch
from .crossref import crossref
from .dois import dois
from .meca import meca


@click.group()
def main() -> None:
    pass


main.add_command(batch)
main.add_command(crossref)
main.add_command(dois)
main.add_command(meca)

if __name__ == '__main__':
    main()
