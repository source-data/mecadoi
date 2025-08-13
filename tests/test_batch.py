from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List
from unittest.mock import Mock, patch

from mecadoi.batch import add_preprint_doi, deposit, parse
from mecadoi.crossref.verify import VerificationResult
from mecadoi.db import DepositionAttempt, ParsedFile
from tests.common import DepositionFileTestCase, MecaArchiveTestCase
from tests.test_article import (
    ARTICLES,
    DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
    PUBLICATION_DATE,
)
from tests.test_db import BatchDbTestCase
from tests.test_meca import MANUSCRIPTS


class BaseBatchTestCase(BatchDbTestCase):
    def assert_timestamps_within_interval(
        self, expected: datetime, actual: datetime, interval: timedelta
    ) -> None:
        self.assertIsNotNone(expected)
        self.assertIsNotNone(actual)
        delta = actual - expected
        self.assertGreaterEqual(interval, delta)


class BaseParseTestCase(MecaArchiveTestCase, BaseBatchTestCase):
    def setUp(self) -> None:
        meca_names_by_status = {
            ParsedFile.Invalid: ["no-article", "no-manifest"],
            ParsedFile.NoReviews: ["no-reviews"],
            ParsedFile.NoDoi: ["no-preprint-doi"],
            ParsedFile.Valid: [
                "multiple-revision-rounds",
                "no-author-reply",
                "no-institution",
                "single-revision-round",
            ],
        }

        self.input_files = self.get_meca_archive_paths(
            [file for files in meca_names_by_status.values() for file in files]
        )

        self.expected_parsed_files = [
            ParsedFile(
                path=self.get_meca_archive_path(meca_name),
                received_at=datetime.now(),
                manuscript=MANUSCRIPTS[meca_name]
                if status != ParsedFile.Invalid
                else None,
                doi=MANUSCRIPTS[meca_name].preprint_doi
                if status != ParsedFile.Invalid
                else None,
                status=status,
            )
            for status, meca_names in meca_names_by_status.items()
            for meca_name in meca_names
        ]

        return super().setUp()

    def assert_parsed_files_in_db(
        self, expected_meca_archives: List[ParsedFile]
    ) -> None:
        meca_archives_in_db = self.db.fetch_all(ParsedFile)
        self.assert_parsed_files_equal(expected_meca_archives, meca_archives_in_db)

    def assert_parsed_files_equal(
        self,
        expected_meca_archives: List[ParsedFile],
        actual_meca_archives: List[ParsedFile],
    ) -> None:
        self.assertEqual(len(expected_meca_archives), len(actual_meca_archives))
        for meca_archive in expected_meca_archives:
            # find the corresponding meca archive from the database
            meca_archive_in_db = [
                m for m in actual_meca_archives if m.path == meca_archive.path
            ][0]
            # make sure the timestamps are roughly equal
            self.assert_timestamps_within_interval(
                meca_archive.received_at,
                meca_archive_in_db.received_at,
                timedelta(minutes=5),
            )

            # We don't care about the id
            meca_archive_in_db.id = meca_archive.id
            # The timestamps are fuzzily compared above
            meca_archive_in_db.received_at = meca_archive.received_at

            self.assertEqual(meca_archive, meca_archive_in_db)


class ParseTestCase(BaseParseTestCase):
    def test_batch_parse(self) -> None:
        """Verifies that all given files are parsed and entered into the database."""
        actual_parsed_files = parse(self.input_files, self.db)

        self.assert_parsed_files_equal(self.expected_parsed_files, actual_parsed_files)
        self.assert_parsed_files_in_db(self.expected_parsed_files)


class BaseDepositTestCase(DepositionFileTestCase, BaseBatchTestCase):
    """Verifies that the mecadoi.batch.deposit function works as expected."""

    def setUp(self) -> None:
        super().setUp()

        input_files = [
            "multiple-revision-rounds",
            "no-author-reply",
            # "no-institution",
            "single-revision-round",
        ]
        parsed_files = [
            ParsedFile(
                path=f"{meca_name}.zip",
                received_at=PUBLICATION_DATE,
                manuscript=MANUSCRIPTS[meca_name],
                doi=MANUSCRIPTS[meca_name].preprint_doi,
                status=ParsedFile.Valid,
            )
            for meca_name in input_files
        ]
        self.db.insert_all(parsed_files)
        self.parsed_files = self.db.fetch_all(ParsedFile)

        self.expected_articles = [ARTICLES[name] for name in input_files]

        def expected_deposition_attempts(
            generation_failed: bool = False,
            deposition_failed: bool = False,
            dry_run: bool = False,
        ) -> List[DepositionAttempt]:
            deposition_attempts = []
            for i, meca_name in enumerate(input_files):
                deposition_attempt = DepositionAttempt(
                    meca=self.parsed_files[i], attempted_at=datetime.now()
                )
                deposition_attempts.append(deposition_attempt)
                if generation_failed:
                    deposition_attempt.status = DepositionAttempt.GenerationFailed
                    continue

                deposition_attempt.deposition = Path(
                    f"tests/resources/expected/{meca_name}.xml"
                ).read_text()

                if dry_run:
                    deposition_attempt.status = DepositionAttempt.Succeeded
                    continue
                deposition_attempt.status = (
                    DepositionAttempt.Failed
                    if deposition_failed
                    else DepositionAttempt.Succeeded
                )
            return deposition_attempts

        self.expected_deposition_attempts = expected_deposition_attempts

    def assert_deposition_attempts_in_db(
        self, expected_deposition_attempts: Iterable[DepositionAttempt]
    ) -> None:
        actual_deposition_attempts = self.db.fetch_all(DepositionAttempt)
        expected_deposition_attempts = [i for i in expected_deposition_attempts]
        self.assert_deposition_attempts_equal(
            expected_deposition_attempts, actual_deposition_attempts
        )

    def assert_deposition_attempts_equal(
        self,
        expected_deposition_attempts: List[DepositionAttempt],
        actual_deposition_attempts: List[DepositionAttempt],
    ) -> None:
        self.assertEqual(
            len(expected_deposition_attempts), len(actual_deposition_attempts)
        )

        for i, expected_deposition_attempt in enumerate(expected_deposition_attempts):
            actual_deposition_attempt = actual_deposition_attempts[i]

            self.assertEqual(
                expected_deposition_attempt.meca, actual_deposition_attempt.meca
            )

            expected_timestamp = expected_deposition_attempt.attempted_at
            actual_timestamp = actual_deposition_attempt.attempted_at
            if expected_timestamp is None or actual_timestamp is None:
                self.assertEqual(expected_timestamp, actual_timestamp)
            else:
                self.assert_timestamps_within_interval(
                    expected_timestamp, actual_timestamp, timedelta(minutes=5)
                )

            expected_deposition_file = expected_deposition_attempt.deposition
            actual_deposition_file = actual_deposition_attempt.deposition
            if expected_deposition_file is None or actual_deposition_file is None:
                self.assertEqual(expected_deposition_file, actual_deposition_file)
            else:
                self.assertDepositionFileEquals(
                    expected_deposition_file, actual_deposition_file
                )
            self.assertEqual(
                expected_deposition_attempt.status,
                actual_deposition_attempt.status,
            )


@patch("mecadoi.batch.deposit_file")
@patch(
    "mecadoi.batch.verify",
    return_value=[
        VerificationResult(
            preprint_doi="preprint_doi",
            all_reviews_present=True,
            author_reply_matches=True,
        )
    ],
)
@patch("mecadoi.batch.get_free_doi", return_value=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES)
class DepositTestCase(BaseDepositTestCase):
    def test_depositing_parsed_files(
        self,
        _verify: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        actual_deposition_attempts, actual_articles = deposit(
            self.parsed_files, self.db, dry_run=False
        )
        expected_deposition_attempts = self.expected_deposition_attempts()
        self.assert_deposition_attempts_equal(
            expected_deposition_attempts, actual_deposition_attempts
        )
        self.assertEqual(self.expected_articles, actual_articles)
        self.assertEqual(len(self.parsed_files), len(deposit_file_mock.mock_calls))
        self.assert_deposition_attempts_in_db(expected_deposition_attempts)

    def test_deposition_fails(
        self,
        _verify: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        deposit_file_mock.side_effect = Exception("Boom!")
        expected_deposition_attempts = self.expected_deposition_attempts(
            deposition_failed=True
        )

        actual_deposition_attempts, actual_articles = deposit(
            self.parsed_files, self.db, dry_run=False
        )

        self.assert_deposition_attempts_equal(
            expected_deposition_attempts, actual_deposition_attempts
        )
        self.assertEqual([], actual_articles)
        self.assert_deposition_attempts_in_db(expected_deposition_attempts)
        self.assertEqual(len(self.parsed_files), len(deposit_file_mock.mock_calls))

    @patch(
        "mecadoi.batch.generate_peer_review_deposition", side_effect=Exception("Boom!")
    )
    def test_deposition_file_generation_fails(
        self,
        _generate_peer_review_deposition: Mock,
        _verify: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        expected_deposition_attempts = self.expected_deposition_attempts(
            generation_failed=True
        )

        actual_deposition_attempts, actual_articles = deposit(
            self.parsed_files, self.db, dry_run=False
        )

        self.assert_deposition_attempts_equal(
            expected_deposition_attempts, actual_deposition_attempts
        )
        self.assertEqual([], actual_articles)
        self.assert_deposition_attempts_in_db(expected_deposition_attempts)
        deposit_file_mock.assert_not_called()

    @patch(
        "mecadoi.batch.get_random_doi", return_value=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES
    )
    def test_dry_run_depositing_parsed_files(
        self,
        _get_random_doi: Mock,
        _verify: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        actual_deposition_attempts, actual_articles = deposit(
            self.parsed_files, self.db, dry_run=True
        )
        expected_deposition_attempts = self.expected_deposition_attempts(dry_run=True)
        self.assert_deposition_attempts_equal(
            expected_deposition_attempts, actual_deposition_attempts
        )
        self.assertEqual([], actual_articles)
        self.assert_deposition_attempts_in_db([])
        deposit_file_mock.assert_not_called()

    def test_depositing_invalid_parsed_files(
        self,
        _verify: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        fixtures = [
            ParsedFile(
                path="path", received_at=datetime.now(), manuscript=manuscript, id=db_id
            )
            for manuscript, db_id in [
                (MANUSCRIPTS["single-revision-round"], None),  # no id
                (None, 20),  # no manuscript
                (MANUSCRIPTS["no-reviews"], 20),  # no reviews
                (MANUSCRIPTS["no-preprint-doi"], 20),  # no preprint DOI
            ]
        ]
        for parsed_file in fixtures:
            with self.subTest(parsed_file=parsed_file):
                parsed_files = [parsed_file] + self.parsed_files
                with self.assertRaises(ValueError):
                    deposit(parsed_files, self.db, dry_run=False)
                deposit_file_mock.assert_not_called()


class AddPreprintDoiTestCase(BaseBatchTestCase):
    """Verifies that the mecadoi.batch.add_preprint_doi function works as expected."""

    def setUp(self) -> None:
        super().setUp()

        parsed_files = (
            [
                ParsedFile(
                    path=f"{meca_name}.zip",
                    received_at=PUBLICATION_DATE,
                    manuscript=MANUSCRIPTS[meca_name],
                    doi=MANUSCRIPTS[meca_name].preprint_doi,
                    status=ParsedFile.Valid,
                )
                for meca_name in [
                    "multiple-revision-rounds",
                    "single-revision-round",
                    "single-revision-round",
                ]
            ]
            + [
                ParsedFile(
                    path="no-preprint-doi.zip",
                    received_at=PUBLICATION_DATE,
                    manuscript=MANUSCRIPTS["no-preprint-doi"],
                    status=ParsedFile.NoDoi,
                ),
                ParsedFile(
                    path="invalid-meca.zip",
                    received_at=PUBLICATION_DATE,
                    status=ParsedFile.Invalid,
                ),
            ]
            + [
                ParsedFile(
                    path=f"duplicate-manuscript-id.{i}.zip",
                    received_at=PUBLICATION_DATE,
                    manuscript=MANUSCRIPTS["no-preprint-doi"],
                    status=ParsedFile.NoDoi,
                )
                for i in range(2)
            ]
        )
        self.db.insert_all(parsed_files)
        self.parsed_files = self.db.fetch_all(ParsedFile)
        self.file_no_doi = next(
            file for file in self.parsed_files if file.status == ParsedFile.NoDoi
        )

    def test_update_preprint_doi_happy_path(self) -> None:
        """Verifies that a preprint DOI can be updated in the database."""
        manuscript_id = "no-preprint-doi"
        doi = "10.1234/updated-doi"

        self.assertEqual(
            self.db.fetch_parsed_files_with_doi(doi),
            [],
            "No existing file with that DOI",
        )

        add_preprint_doi(manuscript_id, doi, self.db, dry_run=False)

        files_with_doi = self.db.fetch_parsed_files_with_doi(doi)
        self.assertEqual(
            len(files_with_doi), 1, "Expected one matching file with that DOI"
        )

        # the DOI is in all fields where it has to go and the status is updated
        updated_file = files_with_doi[0]
        self.assertEqual(updated_file.doi, doi, "ParsedFile.doi must be updated")
        self.assertEqual(
            updated_file.manuscript.preprint_doi if updated_file.manuscript else None,
            doi,
            "ParsedFile.manuscript.preprint_doi must be updated",
        )
        self.assertEqual(
            updated_file.status,
            ParsedFile.Valid,
            "ParsedFile.status must be updated from NoDoi to Valid",
        )

    def test_update_preprint_doi_dry_run(self) -> None:
        """Verifies that dry-run adding a preprint DOI doesn't change the database."""
        manuscript_id = "no-preprint-doi"
        doi = "10.1234/updated-doi"

        self.assertEqual(
            self.db.fetch_parsed_files_with_doi(doi),
            [],
            "No existing file with that DOI",
        )
        add_preprint_doi(manuscript_id, doi, self.db, dry_run=True)
        self.assertEqual(
            self.db.fetch_parsed_files_with_doi(doi),
            [],
            "Dry run should not update the database",
        )

    def test_update_preprint_doi_no_matching_files(self) -> None:
        """Verifies that adding a preprint DOI with no matching files is a no-op."""
        manuscript_id = "nonexistent-manuscript"
        doi = "10.1234/nonexistent-doi"

        self.assertEqual(
            self.db.fetch_parsed_files_with_manuscript_id(manuscript_id),
            [],
            "No existing file with that manuscript ID",
        )

        with self.assertRaises(ValueError) as context:
            add_preprint_doi(manuscript_id, doi, self.db, dry_run=False)
        self.assertIn(
            manuscript_id,
            str(context.exception),
            "The ValueError must mention the manuscript_id",
        )
        self.assertEqual(
            self.db.fetch_parsed_files_with_doi(doi),
            [],
            "Failed update should not update the database",
        )

    def test_update_preprint_doi_multiple_matching_files(self) -> None:
        """Verifies that adding a preprint DOI with multiple matching files updates all of them."""
        manuscript_id = "duplicate-manuscript-id"
        doi = "10.1234/updated-doi"

        self.assertGreater(
            len(self.db.fetch_parsed_files_with_manuscript_id(manuscript_id)),
            1,
            "Multiple files with that manuscript ID must exist",
        )

        with self.assertRaises(ValueError) as context:
            add_preprint_doi(manuscript_id, doi, self.db, dry_run=False)
        self.assertIn(
            manuscript_id,
            str(context.exception),
            "The ValueError must mention the manuscript_id",
        )
        self.assertEqual(
            self.db.fetch_parsed_files_with_doi(doi),
            [],
            "Failed update should not update the database",
        )

    def test_update_preprint_doi_existing_file_with_doi(self) -> None:
        manuscript_id = "no-preprint-doi"
        doi = MANUSCRIPTS["multiple-revision-rounds"].preprint_doi
        if doi is None:
            raise ValueError("Manuscript does not have a preprint DOI.")
        files_with_doi = self.db.fetch_parsed_files_with_doi(doi)
        self.assertEqual(len(files_with_doi), 1, "One existing file with that DOI")

        with self.assertRaises(ValueError) as context:
            add_preprint_doi(manuscript_id, doi, self.db, dry_run=False)
        self.assertIn(
            doi,
            str(context.exception),
            "The ValueError must mention the offending DOI",
        )

        self.assertEqual(
            self.db.fetch_parsed_files_with_doi(doi),
            files_with_doi,
            "Failed update should not change the existing file with that DOI",
        )

    def test_update_preprint_doi_file_not_marked_as_no_doi(self) -> None:
        manuscript_ids = [
            "multiple-revision-rounds",
            "invalid-meca",
            "duplicate-manuscript-id",
        ]
        for manuscript_id in manuscript_ids:
            with self.subTest(manuscript_id=manuscript_id):
                doi = "10.1234/updated-doi"

                self.assertEqual(
                    self.db.fetch_parsed_files_with_doi(doi),
                    [],
                    "No existing file with that DOI",
                )
                with self.assertRaises(ValueError) as context:
                    add_preprint_doi(manuscript_id, doi, self.db, dry_run=False)
                self.assertIn(
                    manuscript_id,
                    str(context.exception),
                    "The ValueError must mention the manuscript_id",
                )
                self.assertEqual(
                    self.db.fetch_parsed_files_with_doi(doi),
                    [],
                    "Failed update should not change the existing file with that DOI",
                )
