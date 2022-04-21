from datetime import datetime
import sqlite3
from src.config import DOI_DB_FILE, DOI_DB_WARNING_THRESHOLD


def get_free_doi(resource: str, doi_db_file: str = DOI_DB_FILE, warning_threshold: int = DOI_DB_WARNING_THRESHOLD):
    """
    Get an unused DOI from the DOI database.

    The `doi_db_file` parameter must be the path to an SQLite3 database that is readable by the DoiDatabase class, and
    has to be have at least one free, i.e. unused, DOI.
    """
    doi_db = DoiDatabase(doi_db_file)

    num_free_dois = doi_db.get_num_free_dois()
    if warning_threshold and num_free_dois < warning_threshold:
        notify_running_low_on_dois(num_free_dois)

    return doi_db.get_free_doi(resource)


def notify_running_low_on_dois(num_free_dois: str):
    print(f'WARNING: running low on DOIs, only {num_free_dois} left!')


class DoiDatabase:
    """
    Interface for accessing a DOI database.

    Create a new database by calling `DoiDatabase(path_to_database).initialize()`. Add new DOIs to an existing database
    by passing a sequence of DOIs to `.insert_dois()`.
    """

    CREATE_TABLE_STATEMENT = """
CREATE TABLE IF NOT EXISTS dois
    (
        doi TEXT,
        resource TEXT,
        claimed_at TIMESTAMP,
        PRIMARY KEY (doi)
    )
"""
    QUERY_FETCH_FREE_DOI = 'SELECT doi FROM dois WHERE resource IS NULL LIMIT 1'
    QUERY_SET_RESOURCE = 'UPDATE dois SET resource = :resource, claimed_at=:timestamp WHERE doi = :doi'
    QUERY_NUM_FREE_DOIS = 'SELECT COUNT(*) FROM dois WHERE resource IS NULL'
    QUERY_NUM_TOTAL_DOIS = 'SELECT COUNT(*) FROM dois'
    QUERY_INSERT_DOIS = 'INSERT INTO dois (doi) VALUES (?)'

    def __init__(self, db_file: str = DOI_DB_FILE) -> None:
        self.db_file = db_file

    def conn(self):
        return sqlite3.connect(self.db_file)

    def get_free_doi(self, resource: str):
        if not resource:
            raise ValueError('Need to pass in resource to get DOI')

        with self.conn() as conn:
            cursor = conn.cursor()
            result = cursor.execute(self.QUERY_FETCH_FREE_DOI).fetchone()
            if result is None:
                raise ValueError('No free DOIs available!')

            doi = result[0]
            timestamp = datetime.now()
            cursor.execute(self.QUERY_SET_RESOURCE, {
                'resource': resource,
                'timestamp': timestamp,
                'doi': doi,
            })

            return doi

    def get_num_free_dois(self):
        with self.conn() as conn:
            result = conn.cursor().execute(self.QUERY_NUM_FREE_DOIS).fetchone()
        return result[0]

    def get_num_total_dois(self):
        with self.conn() as conn:
            result = conn.cursor().execute(self.QUERY_NUM_TOTAL_DOIS).fetchone()
        return result[0]

    def insert_dois(self, dois: dict[str]):
        with self.conn() as conn:
            conn.cursor().executemany(self.QUERY_INSERT_DOIS, [(doi,) for doi in dois])

    def initialize(self):
        with self.conn() as conn:
            conn.cursor().execute(self.CREATE_TABLE_STATEMENT)
