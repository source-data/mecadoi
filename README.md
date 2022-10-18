# MECADOI

Deposit DOIs for peer reviews and authors' reply contained in a MECA archive.

This project consists of a Python library thats reads [Manuscript Exchange Common Approach](https://www.niso.org/standards-committees/meca) (MECA) archives, extracts
the metadata required then register a DOI for each review and, when available, the authors' reply, using the [CrossRef deposition API](https://www.crossref.org/documentation/member-setup/direct-deposit-xml/).

It is currently used in the context of EMBO's [Review Commons](https://www.reviewcommons.org/) and [Early Evidence Base](https://eeb.embo.org/) projects and _would require changes for use in another environment._ \[To be clarified later...\]

## Requirements

For the basic CLI commands:
* `python3` >= 3.9
* `pip`

If you want to register DOIs:
* [CrossRef membership](https://www.crossref.org/documentation/member-setup/) and [CrossRef account]() credentials.

If you only want to test the application, CrossRef provides a [sandbox environment](https://test.crossref.org/) that neeed separate credentials. Note that it might be necessary to first preregister an article DOI before being able to test the deposition of a linked peer review.

_For the requirements for the automated deposition workflows see the Workflows section._

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
python3 -m src.cli.main meca info demo-meca.zip
```

Expected output
```bash
authors: Jane, Doe, John, Doe
doi: 10.12345/multiple-revision-rounds.1234567890
journal: Review Commons - TEST
preprint_doi: 10.1101/multiple-revision-rounds.123.456.7890
review_process: 2 revision rounds, 4 reviews, 1 author reply
title: An article with multiple revision rounds.
```


## Configuration

The application is configured through an env file.
It's location is `.env` by default but can be set through the `ENV_FILE` environment variable like so:

```
ENV_FILE=.env.ci python3 -m src.cli.main [command] [subcommand]
```

The configuration for a specific peer review platform is defined in `config.py`. See details in `documentation/doc.md`.


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

The `meca` and `crossref` commands are for exploration and debugging. The `batch` command is used in the actual deposition workflow.
Each command has its own subcommands:

```
meca
    info
    reviews
crossref
    generate
    verify
batch
    parse
    deposit



Almost every command's output is in the YAML format.

### `meca`

These commands extract and output information from a single MECA archive.

#### `info`

Use the `info` subcommand to get basic information about a MECA archive:

```bash
python3 -m src.cli.main meca info demo-meca.zip
```
This will output the authors, journal, and title of the article, any DOIs, and a summary of the peer review process.
Example:
```
```

#### `reviews`

This outputs detailed information about the peer review process of the article in the MECA archive:

```bash
python3 -m src.cli.main meca reviews demo-meca.zip
```

### `crossref`

These commands are for interaction with the Crossref API.

#### `generate`

This command is useful for debugging and inspection of CrossRef deposition file. It also can be used for manual deposition of peer review DOIs for a single. This takes a MECA archive as input and generates a Crossref deposition file. It contains all the metadata needed to create DOIs for every peer review in the MECA archive.
The DOIs to be used are randomly generated and not checked for uniqueness.
Information such as the registrant and depositor name are taken from the `.env` file.

```bash
python3 -m src.cli.main crossref generate -o deposition.xml demo-meca.zip
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

All actions taken during these commands are recorded in the MECADOI database.
Its location can be set through the `DB_URL` parameter in the `.env` file.

#### `parse`

This command parses MECA archives to extract the relevant metadata and update the MECADOI database.
It takes as input positional parameter the path to the directory containing the MECA archives. This input directory is search recursively.
Every processed MECA archive is saved for further reference to a `parsed/<uuid>/` subfolder within the folder provided with the `-o` option.


```bash
python3 -m src.cli.main batch parse -o output/ input-dir/


```

This subcommand...
1. Moves all files in the given input directory to a new subdirectory in the given output directory.
2. Registers all files in the database.
3. Tries to parse these files as MECA archives and updates the database accordingly with the extracted metadata.

It returns all processed files and their status after parsing.

Example (including failures):
```

```


#### `deposit`

The `deposit` subcommand execute the deposition of multiple CrossRef metadata deposition files. It finds the MECADOI database records for every successfully parsed MECA archive that has reviews & a preprint DOI and for which no DOIs have yet been successfully deposited. Then, for each selected record, a deposition attempt is made and stored in the batch database. 

By default, the command `deposit` will NOT execute the deposition of the DOIS. To actually execute the irreversible deposition and to update the database, the default behavior has to be overriden by explicitly adding the option `--no-dry-run`.

The `deposit` commdand will generate .`yml` file to....

```bash
python3 -m src.cli.main batch deposit -o output/
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
