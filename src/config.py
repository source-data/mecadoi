from dotenv import load_dotenv
from os import getenv

load_dotenv()


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
AUTHOR_REPLY_RESOURCE_URL_TEMPLATE = getenv_or_raise('AUTHOR_REPLY_RESOURCE_URL_TEMPLATE')

DOI_DB_FILE = getenv_or_raise('DOI_DB_FILE')
DOI_TEMPLATE = getenv_or_raise('DOI_TEMPLATE')

CROSSREF_DEPOSITION_URL = getenv_or_raise('CROSSREF_DEPOSITION_URL')
CROSSREF_USERNAME = getenv_or_raise('CROSSREF_USERNAME')
CROSSREF_PASSWORD = getenv_or_raise('CROSSREF_PASSWORD')
