"""
Provides configuration for the application.

The configuration parameters are loaded from a file called ".env" in the working directory. If no such file exists, the
parent folders of the working directory are searched.

The configuration file can also be specified by setting the environment variable ENV_FILE when invoking the application.
"""

from dotenv import load_dotenv
from logging import basicConfig
from os import getenv

# Use the ENV_FILE parameter to load the configuration file. If the parameter isn't set, the dotenv library searches
# for a file called ".env", first in the current folder and then in its parents.
load_dotenv(dotenv_path=getenv('ENV_FILE'))


def getenv_or_raise(name: str) -> str:
    val = getenv(name)
    if val is None:
        raise ValueError(f'no env variable found for name "{name}"')
    return val


DEPOSITOR_NAME = getenv_or_raise('DEPOSITOR_NAME')
DEPOSITOR_EMAIL = getenv_or_raise('DEPOSITOR_EMAIL')
REGISTRANT_NAME = getenv_or_raise('REGISTRANT_NAME')
INSTITUTION_NAME = getenv_or_raise('INSTITUTION_NAME')
REVIEW_RESOURCE_URL_TEMPLATE = getenv_or_raise('REVIEW_RESOURCE_URL_TEMPLATE')
REVIEW_TITLE_TEMPLATE = getenv_or_raise('REVIEW_TITLE_TEMPLATE')
AUTHOR_REPLY_RESOURCE_URL_TEMPLATE = getenv_or_raise('AUTHOR_REPLY_RESOURCE_URL_TEMPLATE')
AUTHOR_REPLY_TITLE_TEMPLATE = getenv_or_raise('AUTHOR_REPLY_TITLE_TEMPLATE')
DOI_TEMPLATE = getenv_or_raise('DOI_TEMPLATE')

DOI_DB_FILE = getenv_or_raise('DOI_DB_FILE')
DB_URL = getenv_or_raise('DB_URL')

CROSSREF_DEPOSITION_URL = getenv_or_raise('CROSSREF_DEPOSITION_URL')
CROSSREF_USERNAME = getenv_or_raise('CROSSREF_USERNAME')
CROSSREF_PASSWORD = getenv_or_raise('CROSSREF_PASSWORD')

LOG_FILE = getenv('LOG_FILE')
LOG_LEVEL = getenv('LOG_LEVEL')

if LOG_FILE:
    level = LOG_LEVEL or 'INFO'
    basicConfig(filename=LOG_FILE, level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

__all__ = [
    'DEPOSITOR_NAME',
    'DEPOSITOR_EMAIL',
    'REGISTRANT_NAME',
    'INSTITUTION_NAME',
    'REVIEW_RESOURCE_URL_TEMPLATE',
    'REVIEW_TITLE_TEMPLATE',
    'AUTHOR_REPLY_RESOURCE_URL_TEMPLATE',
    'AUTHOR_REPLY_TITLE_TEMPLATE',
    'DOI_TEMPLATE',

    'DOI_DB_FILE',
    'DB_URL',

    'CROSSREF_DEPOSITION_URL',
    'CROSSREF_USERNAME',
    'CROSSREF_PASSWORD',

    'LOG_FILE',
    'LOG_LEVEL',
]
