from datetime import datetime
from os import remove
from unittest import TestCase

from src.db import BatchDatabase, ParsedFile
from tests.test_meca import MANUSCRIPTS


class BatchDbTestCase(TestCase):

    def setUp(self) -> None:
        if not hasattr(self, 'db_file'):
            self.db_file = 'tests/tmp/batch.sqlite3'

        try:
            remove(self.db_file)
        except FileNotFoundError:
            pass

        self.db = BatchDatabase(self.db_file)


class DbTestCase(BatchDbTestCase):

    def setUp(self) -> None:
        self.parsed_files = [
            ParsedFile(path='invalid', received_at=datetime.now()),
            ParsedFile(path='incomplete', received_at=datetime.now(), manuscript=MANUSCRIPTS['no-reviews']),
            ParsedFile(path='ready', received_at=datetime.now(), manuscript=MANUSCRIPTS['no-author-reply']),
        ]

        return super().setUp()

    def test_inserting_parsed_files(self) -> None:
        """
        Verify that inserting ParsedFiles works as intended.

        Subsequent calls to `db.get_all_parsed_files()` should return the inserted objects.
        """
        self.db.add_parsed_files(self.parsed_files)

        # Fetching all MecaArchives should return the ones we just inserted.
        inserted_parsed_files = self.db.get_all_parsed_files()
        # Check that the inserted ParsedFiles are returned and now have an id.
        self.assertEqual(len(self.parsed_files), len(inserted_parsed_files))
        for i, parsed_file in enumerate(self.parsed_files):
            inserted_parsed_file = inserted_parsed_files[i]
            self.assertIsNotNone(inserted_parsed_file.id)

            # Add an id to the expected MecaArchive to allow us to use the assertEqual method.
            parsed_file.id = inserted_parsed_file.id
            self.assertEqual(parsed_file, inserted_parsed_file)

    def test_initializing_db_doesnt_erase_existing_db(self) -> None:
        """Re-initializing the database must not overwrite any data already stored in it."""
        self.db.add_parsed_files(self.parsed_files)

        self.db.initialize()

        parsed_files_in_db = self.db.get_all_parsed_files()
        self.assertEqual(len(self.parsed_files), len(parsed_files_in_db))
