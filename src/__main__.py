from click import group

from src.cli.batch import batch
from src.cli.meca import meca


@group()
def main() -> None:
    pass

main.add_command(batch)
main.add_command(meca)

if __name__ == "__main__":
    main()
