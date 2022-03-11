import click
from .crossref import crossref
from .dois import dois
from .meca import meca

@click.group()
def main():
    pass

main.add_command(crossref)
main.add_command(dois)
main.add_command(meca)

if __name__ == '__main__':
    main()