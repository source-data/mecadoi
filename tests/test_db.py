from datetime import datetime
from os import remove
from typing import List
from unittest import TestCase

from mecadoi.db import BatchDatabase, DepositionAttempt, ParsedFile
from tests.test_meca import MANUSCRIPTS


class BatchDbTestCase(TestCase):
    def get_db_file(self) -> str:
        return "tests/tmp/batch.sqlite3"

    def get_db_url(self) -> str:
        return f"sqlite:///{self.get_db_file()}"

    def clear_database(self) -> None:
        try:
            remove(self.get_db_file())
        except FileNotFoundError:
            pass

    def initialize_database(self) -> BatchDatabase:
        db = BatchDatabase(self.get_db_url())
        db.initialize()
        return db

    def setUp(self) -> None:
        db_file = self.get_db_file()
        test_dir = "tests/tmp"
        self.assertTrue(
            db_file.startswith(test_dir),
            f"Are you using the right db file? It should be in {test_dir}",
        )

        self.clear_database()
        self.db = self.initialize_database()


class DbTestCase(BatchDbTestCase):
    def setUp(self) -> None:
        self.parsed_files = [
            ParsedFile(
                path="invalid",
                received_at=datetime(2020, 6, 21),
                status=ParsedFile.Invalid,
            ),
            ParsedFile(
                path="incomplete",
                received_at=datetime(2020, 9, 30),
                manuscript=MANUSCRIPTS["no-reviews"],
                doi=MANUSCRIPTS["no-reviews"].preprint_doi,
                status=ParsedFile.NoReviews,
            ),
            ParsedFile(
                path="ready",
                received_at=datetime(2021, 2, 14),
                manuscript=MANUSCRIPTS["no-author-reply"],
                doi=MANUSCRIPTS["no-author-reply"].preprint_doi,
                status=ParsedFile.Valid,
            ),
            ParsedFile(
                path="deposition-failed",
                received_at=datetime(2021, 11, 5),
                manuscript=MANUSCRIPTS["multiple-revision-rounds"],
                doi=MANUSCRIPTS["multiple-revision-rounds"].preprint_doi,
                status=ParsedFile.Valid,
            ),
            ParsedFile(
                path="deposited",
                received_at=datetime(2022, 1, 1),
                manuscript=MANUSCRIPTS["single-revision-round"],
                doi=MANUSCRIPTS["single-revision-round"].preprint_doi,
                status=ParsedFile.Valid,
            ),
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
                deposition="<deposition_attempt></deposition_attempt>",
                attempted_at=datetime.now(),
                status=DepositionAttempt.Failed,
            ),
            DepositionAttempt(
                meca=inserted_parsed_files[4],
                deposition="<deposition_attempt></deposition_attempt>",
                attempted_at=datetime.now(),
                status=DepositionAttempt.Succeeded,
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
                deposition="<deposition_attempt></deposition_attempt>",
                attempted_at=datetime.now(),
                status=DepositionAttempt.Failed,
            )
            for meca in [
                file_with_failed_attempts,
                file_with_failed_attempts,
                file_with_successful_attempt,
            ]
        ]
        successful_attempts = [
            DepositionAttempt(
                meca=file_with_successful_attempt,
                deposition="<deposition_attempt></deposition_attempt>",
                attempted_at=datetime.now(),
                status=DepositionAttempt.Succeeded,
            )
        ]
        self.db.insert_all(failed_attempts + successful_attempts)

        files_ready_for_deposition = self.db.get_files_ready_for_deposition(
            datetime(1900, 1, 1), datetime.now()
        )
        expected_files_ready_for_deposition = [file_without_attempts]

        self.assertEqual(
            expected_files_ready_for_deposition, files_ready_for_deposition
        )

    def test_get_parsed_files_ready_for_deposition_between(self) -> None:
        self.db.insert_all(self.parsed_files)
        inserted_parsed_files = self.db.fetch_all(ParsedFile)

        actual = self.db.get_files_ready_for_deposition(
            datetime(2021, 1, 1), datetime(2022, 1, 1)
        )
        expected = inserted_parsed_files[2:4]
        self.assertEqual(expected, actual)

    def test_get_files_to_retry_deposition(self) -> None:
        self.db.insert_all(
            self.parsed_files
            + [
                ParsedFile(
                    path="verification-failed",
                    received_at=datetime(2022, 3, 15),
                    manuscript=MANUSCRIPTS["no-author-reply"],
                    doi=MANUSCRIPTS["no-author-reply"].preprint_doi,
                    status=ParsedFile.Valid,
                ),
                ParsedFile(
                    path="dois-already-present",
                    received_at=datetime(2022, 4, 16),
                    manuscript=MANUSCRIPTS["no-author-reply"],
                    doi=MANUSCRIPTS["no-author-reply"].preprint_doi,
                    status=ParsedFile.Valid,
                ),
            ]
        )
        inserted_parsed_files = self.db.fetch_all(ParsedFile)

        file_with_failed_attempts = inserted_parsed_files[3]
        file_with_successful_attempt = inserted_parsed_files[4]
        file_with_failed_verification = inserted_parsed_files[5]
        file_with_dois_already_present = inserted_parsed_files[6]

        failed_attempts = [
            DepositionAttempt(
                meca=meca,
                deposition="<deposition_attempt></deposition_attempt>",
                attempted_at=datetime.now(),
                status=DepositionAttempt.Failed,
            )
            for meca in [
                file_with_failed_attempts,
                file_with_successful_attempt,
            ]
        ]
        successful_attempts = [
            DepositionAttempt(
                meca=file_with_successful_attempt,
                deposition="<deposition_attempt></deposition_attempt>",
                attempted_at=datetime.now(),
                status=DepositionAttempt.Succeeded,
            )
        ]
        failed_verification = [
            DepositionAttempt(
                meca=file_with_failed_verification,
                deposition="<deposition_attempt></deposition_attempt>",
                attempted_at=datetime.now(),
                status=DepositionAttempt.VerificationFailed,
            )
        ]
        dois_already_present = [
            DepositionAttempt(
                meca=file_with_dois_already_present,
                deposition="<deposition_attempt></deposition_attempt>",
                attempted_at=datetime.now(),
                status=DepositionAttempt.DoisAlreadyPresent,
            )
        ]
        self.db.insert_all(
            failed_attempts
            + successful_attempts
            + failed_verification
            + dois_already_present
        )

        files_ready_for_deposition = self.db.get_files_to_retry_deposition(
            datetime(1900, 1, 1), datetime.now()
        )
        expected_files_ready_for_deposition = [
            file_with_failed_attempts,
            file_with_failed_verification,
        ]

        self.assertEqual(
            expected_files_ready_for_deposition, files_ready_for_deposition
        )

    def test_get_parsed_files_with_doi(self) -> None:
        self.db.insert_all(self.parsed_files)
        inserted_parsed_files = self.db.fetch_all(ParsedFile)

        for parsed_file in inserted_parsed_files:
            actual = self.db.fetch_parsed_files_with_doi(parsed_file.doi)
            self.assertEqual([parsed_file], actual)

    def test_get_parsed_files_between(self) -> None:
        self.db.insert_all(self.parsed_files)

        expected_parsed_files = self.parsed_files[2:4]
        actual_parsed_files = self.db.fetch_parsed_files_between(
            datetime(2021, 1, 1), datetime(2022, 1, 1)
        )
        self.assert_parsed_files_equal(expected_parsed_files, actual_parsed_files)

    def assert_parsed_files_equal(
        self, expected: List[ParsedFile], actual: List[ParsedFile]
    ) -> None:
        # Check that the inserted ParsedFiles are returned and now have an id.
        self.assertEqual(len(expected), len(actual))
        for i, parsed_file in enumerate(expected):
            inserted_parsed_file = actual[i]
            self.assertIsNotNone(inserted_parsed_file.id)

            # Add an id to the expected ParsedFile to allow us to use the assertEqual method.
            parsed_file.id = inserted_parsed_file.id
            self.assertEqual(parsed_file, inserted_parsed_file)
