# MECADOI

Deposit DOIs for peer reviews in MECA archives.

This project consists of a Python library thats reads [Manuscript Exchange Common Approach](https://www.niso.org/standards-committees/meca) (MECA) archives, extracts
the metadata of any peer reviews within, and then creates a DOI for each review using the [CrossRef deposition API](https://www.crossref.org/documentation/member-setup/direct-deposit-xml/).

It is currently used in the context of EMBO's [Review Commons](https://www.reviewcommons.org/) and [Early Evidence Base](https://eeb.embo.org/) projects and would require changes for use in another environment.

## Requirements

For the basic CLI commands:
* `python3` >= 3.9
* `pip`

If you want to register DOIs:
* [CrossRef account](https://www.crossref.org/documentation/member-setup/) credentials

For the requirements for the automated deposition workflows see the Workflows section.

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

## Configuration

The application is configured through an env file.
It's location is `.env` by default but can be set through the `ENV_FILE` environment variable like so:

```
ENV_FILE=.env.ci python3 -m src.cli.main [command] [subcommand]
```

## CLI

You can explore the command line interface by adding the `--help` parameter to any command to see its usage instructions and subcommands:
```bash
python3 -m src.cli.main --help
python3 -m src.cli.main meca --help
python3 -m src.cli.main meca info --help
```

The CLI has three groups of subcommands:
- `meca` for getting basic information about a single MECA archive
- `crossref` to generate a deposition file from a MECA archive and send it to the Crossref API
- `batch` to perform the MECA parsing, deposition file generation, & interaction with the Crossref API for multiple MECA archives.

Almost every command's output is in the YAML format.

### `meca`

These commands extract and output information from a single MECA archive.

#### `info`

Use the `info` subcommand to get basic information about a MECA archive:

```bash
python3 -m src.cli.main meca info meca-archive.zip
```
This will output the authors, journal, and title of the article, any DOIs, and a summary of the peer review process.

#### `reviews`

This outputs detailed information about the peer review process of the article in the MECA archive:

```bash
python3 -m src.cli.main meca reviews meca-archive.zip
```

### `crossref`

These commands are for interaction with the Crossref API.

#### `generate`

This generates and outputs a Crossref deposition file that can be used to create DOIs for every peer review in the MECA archive.
The DOIs to be used are randomly generated and not checked for uniqueness.
Information such as the registrant and depositor name are taken from the `.env` file.

```bash
python3 -m src.cli.main crossref generate -o deposition.xml meca-archive.zip
```

#### `verify`

Generated deposition files can be sanity-checked with `verify`:
```bash
python3 -m src.cli.main crossref verify deposition.xml
```

Each review in the given deposition file indicates which article it reviews.
This command queries the Early Evidence Base (EEB) API for all articles under review in the given deposition file.
For each article, the command checks whether the reviews and responses available from the EEB API exactly match the reviews and responses in the deposition file.
It also checks whether the EEB API already has DOIs for at least one of these reviews.
As an example, if the deposition file has 3 reviews and 1 author reply belonging to article 10.1234/5678, this command returns an error:
- If EEB doesn't have exactly 3 reviews and 1 author reply for this article.
- If one of these reviews or the reply already has a DOI on EEB.

### `batch`

These commands are for processing multiple MECA archives.

All actions taken during these commands are recorded in an sqlite database.
Its location can be set through the `DB_URL` parameter in the `.env` file.

Some commands have a `--no-dry-run` option: only if this option is passed are irreversible actions taken and is the database updated.
An example is the `deposit` command: by default, no DOIs are actually deposited.
Only by adding `--no-dry-run` is this irreversible action taken and recorded in the database.

#### `parse`

```bash
python3 -m src.cli.main batch parse -o output/ input-dir/
```

This subcommand...
1. Moves all files in the given input directory to a new subdirectory in the given output directory.
2. Registers all files in the database.
3. Tries to parse these files as MECA archives.

It returns all processed files and their status after parsing.


#### `deposit`

The `deposit` subcommand finds every successfully parsed MECA archive in the batch database that has reviews & a preprint DOI and for which no DOIs have been successfully deposited. Then, for each file a deposition attempt is made and stored in the batch database.

Generated deposition files can then be sent to Crossref for DOI creation with the `deposit` command:

```bash
python3 -m src.cli.main batch parse -o output/ input-dir/
```

The Crossref API almost always returns a message indicating success even with obvious mistakes such as malformed DOIs.
They do send an email with detailed information about every submission to the `<depositor>`'s `<email_address>` in the deposition XML.
This address is taken from the `DEPOSITOR_EMAIL` variable in the `.env` file when calling the `generate` subcommand.

## Workflow Pipeline

The MECA processing workflow is currently defined as a series of cron jobs that are set up on a server through the Ansible playbook in [provisioning](provisioning). See the README in that folder for installation details.

The workflow consists of these steps:

1. Move files from the input FTP directory to a local directory.
2. Archive the files to an S3 bucket.
3. Try parsing the files as MECA archives, register them in a database, and archive the processed files.
4. Find all files in that database that are ready to be deposited and deposit them.
5. Export information about the created DOIs.

## Development

Run `pip install -r requirements/dev.txt` to install all development dependencies.

Continuous Integration is run with a Github Actions workflow that is defined in [.github/workflows/unit-tests.yml](.github/workflows/unit-tests.yml).
The workflow lints and tests the application.

### Linting

Checking the code style, formatting, and types is performed with [`flake8`](https://flake8.pycqa.org/en/latest/), [`black`](https://black.readthedocs.io/en/stable/index.html), and [`mypy`](https://mypy.readthedocs.io/), respectively.

`scripts/lint.sh` runs the three tools in succession.

Configuration for flake8 and mypy is in [`.flake8`](.flake8) and [`mypy.ini`](mypy.ini).

### Testing

Tests are located in `tests`, test data (including the contents of some sample MECA archives) in `tests/resources`.

To run all tests:
```bash
python3 -m unittest
```
