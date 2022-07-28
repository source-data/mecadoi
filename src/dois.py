"""Handles the creation of random DOIs and tries to ensure they are not reused."""

__all__ = ['get_random_doi', 'get_free_doi']

from datetime import datetime
from secrets import choice
from string import digits, Template
from sqlite3 import connect, Connection, IntegrityError
from src.config import DOI_DB_FILE, DOI_TEMPLATE


def get_free_doi(resource: str) -> str:
    """
    Get an unused DOI for the given resource.

    The DOIs are created according to the template defined in the DOI_TEMPLATE configuration parameter. The template
    must contain two $-substitution parameters called "year" and "random" which will be replaced with the current year
    and a string of 6 random digits, respectively. For example, the template "10.15252/rc.$year$random" produces DOIs
    like "10.15252/rc.2022123456".

    The DOI that this function returns is stored, with the given resource and a timestamp, in the DOI database. It's
    an sqlite3 database located at the path set in the DOI_DB_FILE configuration parameter.

    IMPORTANT: wether a DOI is unused depends solely on wether it has already been marked as used in the currently
    configured DOI database. Therefore, if the database or its contents are modified, or a different database is
    configured, a previously used DOI may be returned by this function.

    The function will try multiple times to create a random, unused DOI. If it still fails to create an unused DOI
    after these attempt, an Exception is raised.
    """
    doi_db = DoiDatabase(DOI_DB_FILE)
    doi_db.initialize()

    doi = None
    max_num_tries = 10
    num_tries = 0
    while doi is None and num_tries < max_num_tries:
        num_tries += 1
        doi = _create_random_doi()
        try:
            doi_db.mark_doi_as_used(doi, resource)
        except IntegrityError:
            # this means the DOI has already been used
            doi = None
    if doi is None:
        raise Exception(f'failed to generate unused DOI in {max_num_tries} tries')

    return doi


def get_random_doi(_: str) -> str:
    return _create_random_doi()


def _create_random_doi() -> str:
    # create the random part of the DOI: a string of 6 random digits
    population = digits
    k = 6
    random_part = ''.join([choice(population) for i in range(k)])
    year = str(datetime.now().year)
    return Template(DOI_TEMPLATE).substitute(year=year, random=random_part)


class DoiDatabase:
    """Interface for accessing a DOI database."""

    CREATE_TABLE_STATEMENT = """
CREATE TABLE IF NOT EXISTS dois
    (
        doi TEXT,
        resource TEXT,
        claimed_at TIMESTAMP,
        PRIMARY KEY (doi)
    )
"""
    QUERY_INSERT_DOI = 'INSERT INTO dois (doi, resource, claimed_at) VALUES (:doi, :resource, :timestamp)'
    QUERY_NUM_TOTAL_DOIS = 'SELECT COUNT(*) FROM dois'

    def __init__(self, db_file: str = DOI_DB_FILE) -> None:
        self.db_file = db_file

    def conn(self) -> Connection:
        return connect(self.db_file)

    def mark_doi_as_used(self, doi: str, resource: str) -> None:
        with self.conn() as conn:
            params = {
                'doi': doi,
                'resource': resource,
                'timestamp': datetime.now(),
            }
            conn.cursor().execute(self.QUERY_INSERT_DOI, params)

    def get_num_total_dois(self) -> int:
        with self.conn() as conn:
            result = conn.cursor().execute(self.QUERY_NUM_TOTAL_DOIS).fetchone()
        return int(result[0])

    def initialize(self) -> None:
        with self.conn() as conn:
            conn.cursor().execute(self.CREATE_TABLE_STATEMENT)
