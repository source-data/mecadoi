# MECADOI

Deposit DOIs for peer reviews in MECA archives.

This project consists of Python library thats reads [Manuscript Exchange Common Approach](https://www.niso.org/standards-committees/meca) (MECA) archives, extracts
the metadata of any peer reviews within, and then creates a DOI for each review using the [CrossRef deposition API](https://www.crossref.org/documentation/member-setup/direct-deposit-xml/).

It is currently used in the context of EMBO's [Review Commons](https://www.reviewcommons.org/) and [Early Evidence Base](https://eeb.embo.org/) projects and would require
changes for use in another environment.

## Requirements

* `python3` >= 3.9, `pip`
* [CrossRef account](https://www.crossref.org/documentation/member-setup/) credentials if you want to register DOIs

## Quick Start

Clone this repository, create a virtual env (optional), and install the dependencies:
```
git clone https://github.com/source-data/mecadoi.git && cd mecadoi
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### CLI

Get basic information about a MECA archive:
```
python3 -m src.cli.mecadoi -m src/test/test_data/mutagenesis.zip
```

Generate a CrossRef deposition file:
```
python3 -m src.cli.mecadoi generate -m src/test/test_data/mutagenesis.zip -o deposition.xml
```

### Python libary

Read a MECA archive
```python
from zipfile import ZipFile
from src.meca import MECArchive

with ZipFile('src/test/test_data/mutagenesis.zip', 'r') as archive:
        meca = MECArchive(archive, strict_validation=strict_validation)
```

Print some basic information:
```python
print(meca)
```

Generate a CrossRef deposition file:
```python
generate_peer_review_deposition(meca, 'deposition.xml')
```

## Testing

Tests are located in `src/test`, test data (including some sample MECA archives) in `src/test/test_data`.

To run all tests:
```
python3 -m unittest
```