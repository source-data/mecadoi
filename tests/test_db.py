from datetime import datetime
from os import remove
from typing import List
from unittest import TestCase

from src.db import BatchDatabase, DepositionAttempt, ParsedFile
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
            ParsedFile(path='invalid', received_at=datetime(2020, 6, 21)),
            ParsedFile(path='incomplete', received_at=datetime(2020, 9, 30), manuscript=MANUSCRIPTS['no-reviews']),
            ParsedFile(path='ready', received_at=datetime(2021, 2, 14), manuscript=MANUSCRIPTS['no-author-reply']),
            ParsedFile(path='deposition-failed', received_at=datetime(2021, 11, 5),
                       manuscript=MANUSCRIPTS['multiple-revision-rounds']),
            ParsedFile(path='deposited', received_at=datetime(2022, 1, 1),
                       manuscript=MANUSCRIPTS['single-revision-round']),
        ]

        return super().setUp()

    def test_inserting_parsed_files(self) -> None:
        """
        Verify that inserting ParsedFiles works as intended.

        Subsequent calls to `db.fetch_all(ParsedFile)` should return the inserted objects.
        """
        self.db.insert_all(self.parsed_files)

        # Fetching all ParsedFiles should return the ones we just inserted.
        inserted_parsed_files = self.db.fetch_all(ParsedFile)
        self.assert_parsed_files_equal(self.parsed_files, inserted_parsed_files)

    def test_initializing_db_doesnt_erase_existing_db(self) -> None:
        """Re-initializing the database must not overwrite any data already stored in it."""
        self.db.insert_all(self.parsed_files)

        self.db.initialize()

        parsed_files_in_db = self.db.fetch_all(ParsedFile)
        self.assertEqual(len(self.parsed_files), len(parsed_files_in_db))

    def test_inserting_deposition_attempts(self) -> None:
        """
        Verify that inserting DepositionAttempts works as intended.

        Subsequent calls to `db.fetch_all(DepositionAttempt)` should return the inserted objects.
        """
        self.db.insert_all(self.parsed_files)
        inserted_parsed_files = self.db.fetch_all(ParsedFile)

        deposition_attempts = [
            DepositionAttempt(
                meca=inserted_parsed_files[1],
            ),
            DepositionAttempt(
                meca=inserted_parsed_files[3],
                deposition='<deposition_attempt></deposition_attempt>',
                attempted_at=datetime.now(),
                succeeded=False,
            ),
            DepositionAttempt(
                meca=inserted_parsed_files[4],
                deposition='<deposition_attempt></deposition_attempt>',
                attempted_at=datetime.now(),
                succeeded=True,
            ),
        ]
        self.db.insert_all(deposition_attempts)

        # Fetching all MecaArchives should return the ones we just inserted.
        inserted_deposition_attempts = self.db.fetch_all(DepositionAttempt)

        self.assertEqual(len(deposition_attempts), len(inserted_deposition_attempts))
        for i, deposition_attempt in enumerate(deposition_attempts):
            inserted_deposition_attempt = inserted_deposition_attempts[i]
            self.assertIsNotNone(inserted_deposition_attempt.id)

            # Add an id to the expected MecaArchive to allow us to use the assertEqual method.
            deposition_attempt.id = inserted_deposition_attempt.id
            self.assertEqual(deposition_attempt, inserted_deposition_attempt)

    def test_get_parsed_files_ready_for_deposition(self) -> None:
        self.db.insert_all(self.parsed_files)
        inserted_parsed_files = self.db.fetch_all(ParsedFile)

        file_without_attempts = inserted_parsed_files[2]
        file_with_failed_attempts = inserted_parsed_files[3]
        file_with_successful_attempt = inserted_parsed_files[4]

        failed_attempts = [
            DepositionAttempt(
                meca=meca,
                deposition='<deposition_attempt></deposition_attempt>',
                attempted_at=datetime.now(),
                succeeded=False,
            )
            for meca in [file_with_failed_attempts, file_with_failed_attempts, file_with_successful_attempt]
        ]
        successful_attempts = [
            DepositionAttempt(
                meca=file_with_successful_attempt,
                deposition='<deposition_attempt></deposition_attempt>',
                attempted_at=datetime.now(),
                succeeded=True,
            )
        ]
        self.db.insert_all(failed_attempts + successful_attempts)

        files_ready_for_deposition = self.db.get_files_ready_for_deposition(datetime(1900, 1, 1), datetime.now())
        expected_files_ready_for_deposition = [file_without_attempts]

        self.assertEqual(expected_files_ready_for_deposition, files_ready_for_deposition)

    def test_get_parsed_files_ready_for_deposition(self) -> None:
        self.db.insert_all(self.parsed_files)
        inserted_parsed_files = self.db.fetch_all(ParsedFile)

        actual = self.db.get_files_ready_for_deposition(datetime(2021, 1, 1), datetime(2022, 1, 1))
        expected = inserted_parsed_files[2:4]
        self.assertEqual(expected, actual)

    def test_get_parsed_files_between(self) -> None:
        self.db.insert_all(self.parsed_files)

        expected_parsed_files = self.parsed_files[2:4]
        actual_parsed_files = self.db.fetch_parsed_files_between(datetime(2021, 1, 1), datetime(2022, 1, 1))
        self.assert_parsed_files_equal(expected_parsed_files, actual_parsed_files)

    def assert_parsed_files_equal(self, expected: List[ParsedFile], actual: List[ParsedFile]) -> None:
        # Check that the inserted ParsedFiles are returned and now have an id.
        self.assertEqual(len(expected), len(actual))
        for i, parsed_file in enumerate(expected):
            inserted_parsed_file = actual[i]
            self.assertIsNotNone(inserted_parsed_file.id)

            # Add an id to the expected ParsedFile to allow us to use the assertEqual method.
            parsed_file.id = inserted_parsed_file.id
            self.assertEqual(parsed_file, inserted_parsed_file)
