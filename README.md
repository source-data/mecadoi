# MECADOI

Deposit DOIs for peer reviews in MECA archives.

This project consists of a Python library thats reads [Manuscript Exchange Common Approach](https://www.niso.org/standards-committees/meca) (MECA) archives, extracts
the metadata of any peer reviews within, and then creates a DOI for each review using the [CrossRef deposition API](https://www.crossref.org/documentation/member-setup/direct-deposit-xml/).

It is currently used in the context of EMBO's [Review Commons](https://www.reviewcommons.org/) and [Early Evidence Base](https://eeb.embo.org/) projects and would require
changes for use in another environment.

## Requirements

* `python3` >= 3.9, `pip`
* [CrossRef account](https://www.crossref.org/documentation/member-setup/) credentials if you want to register DOIs

## Quick Start

Clone this repository, create a virtual env (optional), and install the dependencies:
```bash
git clone https://github.com/source-data/mecadoi.git && cd mecadoi
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements/base.txt
```

Set up your `.env` file:
```bash
cp .env.example .env
```

You're now ready to use the CLI to get basic info about a MECA archive:

```bash
python3 -m src.cli.main meca info meca-archive.zip
```

## CLI

You can explore the command line interface by adding the `--help` parameter to any command to see its usage instructions and subcommands:
```bash
python3 -m src.cli.main --help
python3 -m src.cli.main meca --help
python3 -m src.cli.main meca info --help
```

The CLI has four groups of subcommands:
- `meca` for getting basic information about a single MECA archive
- `crossref` to generate a deposition file from a MECA archive and send it to the Crossref API
- `batch` to perform the MECA parsing, deposition file generation, & interaction with the Crossref API for multiple MECA archives.

### `meca`

Use the `info` subcommand to get basic information about a MECA archive:
```bash
python3 -m src.cli.main meca info src/test/test_data/mutagenesis.zip
```
This will output the title of the article, any DOIs, the publisher, and the year of publishing.

`reviews` prints the authors and completion dates of any reviews in the MECA archive:
```bash
python3 -m src.cli.main meca reviews src/test/test_data/mutagenesis.zip
```

### `crossref`
Generate a CrossRef deposition file:
```bash
python3 -m src.cli.main crossref generate -o deposition.xml src/test/test_data/mutagenesis.zip
```
This generates a Crossref deposition file that can be used to create DOIs for every peer review in the MECA archive. The DOIs to be used are taken from the DOI database, and information such as the registrant and depositor name are taken from the `.env` file.

Generated deposition files can then be sent to Crossref for DOI creation with the `deposit` command:
```bash
python3 -m src.cli.main crossref deposit deposition.xml
```
The Crossref API almost always returns a message indicating success even with obvious mistakes such as malformed DOIs. They do send an email with detailed information about every submission to the `<depositor>`'s `<email_address>` in the deposition XML, which can be set through the `DEPOSITOR_EMAIL` variable in the `.env` file.

### `batch`

The `deposit` subcommand finds all `.zip` files in the given input directory and tries to parse them as MECA archives. For every successfully parsed MECA archive that has reviews, a deposition file is generated in the given output directory. Then, if `--no-dry-run` is passed, all generated deposition files are sent to the Crossref API.

```bash
python3 -m src.cli.main batch deposit -o output/ input-dir/
```

## Development

Run `pip install -r requirements/dev.txt` to install all development dependencies.

Continuous Integration is run with a Github Actions workflow that is defined in [.github/workflows/unit-tests.yml](.github/workflows/unit-tests.yml).

### Linting & Type Checking

Lint with [`flake8`](https://flake8.pycqa.org/en/latest/):

```bash
flake8
```

Type-check with [`mypy`](https://mypy.readthedocs.io/):

```bash
mypy .
```

The configuration for both is in [`.flake8`](.flake8) and [`mypy.ini`](mypy.ini), respectively.

### Testing

Tests are located in `src/test`, test data (including some sample MECA archives) in `src/test/test_data`.

To run all tests:
```bash
python3 -m unittest
```

## Deployment

The Ansible playbook [`provisioning/provision.yml`](provisioning/provision.yml) sets up the `mecadoi` server defined in [`provisioning/inventory`](provisioning/inventory) from scratch.
