import os
from unittest import TestCase

from src.crossref.dois import DoiDatabase

class DoiDbTestCase(TestCase):

    DOIS = [f'12.3456/7890{i}' for i in range(100)]
    DOI_DB_FILE = 'src/test/tmp/dois.sqlite3'

    def setUp(self) -> None:
        try:
            os.remove(self.DOI_DB_FILE)
        except FileNotFoundError:
            pass

        doi_db = DoiDatabase(self.DOI_DB_FILE)
        doi_db.initialize()
        doi_db.insert_dois(self.DOIS)