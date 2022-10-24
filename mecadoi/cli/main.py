from click import group

from .batch import batch
from .crossref import crossref
from .meca import meca


@group()
def main() -> None:
    pass


main.add_command(batch)
main.add_command(crossref)
main.add_command(meca)

if __name__ == "__main__":
    main()
