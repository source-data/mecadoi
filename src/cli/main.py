from logging import basicConfig
from click import group

from src.config import LOG_FILE, LOG_LEVEL
from .batch import batch
from .crossref import crossref
from .meca import meca


@group()
def main() -> None:
    pass


main.add_command(batch)
main.add_command(crossref)
main.add_command(meca)

if __name__ == '__main__':
    if LOG_FILE:
        basicConfig(filename=LOG_FILE, level=LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
