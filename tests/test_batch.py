from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Iterable, List
from unittest.mock import Mock, patch

from src.batch import DepositedMECAs, deposit, parse, ParsedFiles
from src.crossref.verify import VerificationResult
from src.db import DepositionAttempt, ParsedFile
from tests.common import DepositionFileTestCase, MecaArchiveTestCase
from tests.test_article import ARTICLES, DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES, PUBLICATION_DATE
from tests.test_db import BatchDbTestCase
from tests.test_meca import MANUSCRIPTS


class ParsedFileStatus(Enum):
    INVALID = auto()
    NO_REVIEWS = auto()
    NO_PREPRINT_DOI = auto()
    READY_FOR_DEPOSITION = auto()


class BaseBatchTestCase(BatchDbTestCase):

    def assert_timestamps_within_interval(self, expected: datetime, actual: datetime, interval: timedelta) -> None:
        self.assertIsNotNone(expected)
        self.assertIsNotNone(actual)
        delta = actual - expected
        self.assertGreaterEqual(interval, delta)


class BaseParseTestCase(MecaArchiveTestCase, BaseBatchTestCase):

    def setUp(self) -> None:
        meca_names_by_status = {
            ParsedFileStatus.INVALID: ['no-article', 'no-manifest'],
            ParsedFileStatus.NO_REVIEWS: ['no-reviews'],
            ParsedFileStatus.NO_PREPRINT_DOI: ['no-preprint-doi'],
            ParsedFileStatus.READY_FOR_DEPOSITION: [
                'multiple-revision-rounds',
                'no-author-reply',
                'single-revision-round',
            ],
        }

        self.input_files = self.get_meca_archive_paths([
            file
            for files in meca_names_by_status.values()
            for file in files
        ])

        self.expected_output = ParsedFiles(
            invalid=self.get_meca_archive_paths(meca_names_by_status[ParsedFileStatus.INVALID]),
            no_reviews=self.get_meca_archive_paths(meca_names_by_status[ParsedFileStatus.NO_REVIEWS]),
            no_preprint_doi=self.get_meca_archive_paths(meca_names_by_status[ParsedFileStatus.NO_PREPRINT_DOI]),
            ready_for_deposition=self.get_meca_archive_paths(
                meca_names_by_status[ParsedFileStatus.READY_FOR_DEPOSITION]),
        )
        self.expected_db_contents = [
            ParsedFile(
                path=self.get_meca_archive_path(meca_name),
                received_at=datetime.now(),
                manuscript=MANUSCRIPTS[meca_name] if status != ParsedFileStatus.INVALID else None
            )
            for status, meca_names in meca_names_by_status.items()
            for meca_name in meca_names
        ]

        return super().setUp()

    def assert_meca_archives_in_db(self, expected_meca_archives: List[ParsedFile]) -> None:
        meca_archives_in_db = self.db.fetch_all(ParsedFile)

        self.assertEqual(len(expected_meca_archives), len(meca_archives_in_db))
        for meca_archive in expected_meca_archives:
            # find the corresponding meca archive from the database
            meca_archive_in_db = [m for m in meca_archives_in_db if m.path == meca_archive.path][0]
            # make sure the timestamps are roughly equal
            self.assert_timestamps_within_interval(meca_archive.received_at, meca_archive_in_db.received_at,
                                                   timedelta(minutes=5))

            # We don't care about the id
            meca_archive_in_db.id = meca_archive.id
            # The timestamps are fuzzily compared above
            meca_archive_in_db.received_at = meca_archive.received_at

            self.assertEqual(meca_archive, meca_archive_in_db)

    def assert_results_equal(self, expected: ParsedFiles, actual: ParsedFiles) -> None:
        self.assertEqual(expected, actual)


class ParseTestCase(BaseParseTestCase):

    def test_batch_parse(self) -> None:
        """Verifies that all given files are parsed and entered into the database."""
        actual_output = parse(self.input_files, self.db)

        self.assert_results_equal(self.expected_output, actual_output)
        self.assert_meca_archives_in_db(self.expected_db_contents)


class BaseDepositTestCase(DepositionFileTestCase, BaseBatchTestCase):
    """Verifies that the src.batch.deposit function works as expected."""

    def setUp(self) -> None:
        super().setUp()

        input_files = ['multiple-revision-rounds', 'no-author-reply', 'single-revision-round']
        parsed_files = [
            ParsedFile(path=f'{meca_name}.zip', received_at=PUBLICATION_DATE, manuscript=MANUSCRIPTS[meca_name])
            for meca_name in input_files
        ]
        self.db.insert_all(parsed_files)
        self.parsed_files = self.db.fetch_all(ParsedFile)

        self.expected_output = DepositedMECAs(
            deposition_generation_failed=[],
            deposition_failed=[],
            deposition_succeeded=[p.path for p in self.parsed_files],
        )

        self.expected_articles = [ARTICLES[name] for name in input_files]

        def expected_deposition_attempts(
            generation_failed: bool = False,
            deposition_failed: bool = False
        ) -> Iterable[DepositionAttempt]:
            deposition_attempts = []
            for i, meca_name in enumerate(input_files):
                deposition_attempt = DepositionAttempt(meca=self.parsed_files[i])
                deposition_attempts.append(deposition_attempt)
                if generation_failed:
                    continue

                deposition_attempt.deposition = Path(f'tests/resources/expected/{meca_name}.xml').read_text()
                deposition_attempt.attempted_at = datetime.now()
                deposition_attempt.succeeded = False if deposition_failed else True
            return deposition_attempts

        self.expected_deposition_attempts = expected_deposition_attempts

    def assert_deposition_attempts_in_db(self, expected_deposition_attempts: Iterable[DepositionAttempt]) -> None:
        actual_deposition_attempts = self.db.fetch_all(DepositionAttempt)
        expected_deposition_attempts = [i for i in expected_deposition_attempts]
        self.assertEqual(len(expected_deposition_attempts), len(actual_deposition_attempts))

        for i, expected_deposition_attempt in enumerate(expected_deposition_attempts):
            actual_deposition_attempt = actual_deposition_attempts[i]

            self.assertEqual(expected_deposition_attempt.meca, actual_deposition_attempt.meca)

            expected_timestamp = expected_deposition_attempt.attempted_at
            actual_timestamp = actual_deposition_attempt.attempted_at
            if expected_timestamp is None or actual_timestamp is None:
                self.assertEqual(expected_timestamp, actual_timestamp)
            else:
                self.assert_timestamps_within_interval(expected_timestamp, actual_timestamp, timedelta(minutes=5))

            expected_deposition_file = expected_deposition_attempt.deposition
            actual_deposition_file = actual_deposition_attempt.deposition
            if expected_deposition_file is None or actual_deposition_file is None:
                self.assertEqual(expected_deposition_file, actual_deposition_file)
            else:
                self.assertDepositionFileEquals(expected_deposition_file, actual_deposition_file)
            self.assertEqual(expected_deposition_attempt.succeeded, actual_deposition_attempt.succeeded)


@patch('src.batch.deposit_file')
@patch('src.batch.verify', return_value=[
    VerificationResult(preprint_doi="preprint_doi", all_reviews_present=True, author_reply_matches=True)
])
@patch('src.batch.get_free_doi', return_value=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES)
class DepositTestCase(BaseDepositTestCase):

    def test_depositing_parsed_files(
        self,
        _verify: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        actual_output, actual_articles = deposit(self.parsed_files, self.db, dry_run=False)

        self.assertEqual(self.expected_output, actual_output)
        self.assertEqual(self.expected_articles, actual_articles)
        self.assertEqual(3, len(deposit_file_mock.mock_calls))
        self.assert_deposition_attempts_in_db(self.expected_deposition_attempts())

    def test_deposition_fails(
        self,
        _verify: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        deposit_file_mock.side_effect = Exception('Boom!')
        expected_output = DepositedMECAs(deposition_failed=self.expected_output.deposition_succeeded)

        actual_output, actual_articles = deposit(self.parsed_files, self.db, dry_run=False)

        self.assertEqual(expected_output, actual_output)
        self.assertEqual([], actual_articles)
        self.assert_deposition_attempts_in_db(self.expected_deposition_attempts(deposition_failed=True))
        self.assertEqual(3, len(deposit_file_mock.mock_calls))

    @patch('src.batch.generate_peer_review_deposition', side_effect=Exception('Boom!'))
    def test_deposition_file_generation_fails(
        self,
        _generate_peer_review_deposition: Mock,
        _verify: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        expected_output = DepositedMECAs(deposition_generation_failed=self.expected_output.deposition_succeeded)

        actual_output, actual_articles = deposit(self.parsed_files, self.db, dry_run=False)

        self.assertEqual(expected_output, actual_output)
        self.assertEqual([], actual_articles)
        self.assert_deposition_attempts_in_db(self.expected_deposition_attempts(generation_failed=True))
        # get_free_doi_mock.assert_not_called()
        deposit_file_mock.assert_not_called()

    def test_dry_run_depositing_parsed_files(
        self,
        _verify: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        actual_output, actual_articles = deposit(self.parsed_files, self.db, dry_run=True)
        self.assertEqual(self.expected_output, actual_output)
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
            ParsedFile(path='path', received_at=datetime.now(), manuscript=manuscript, id=db_id)
            for manuscript, db_id in [
                (MANUSCRIPTS['single-revision-round'], None),  # no id
                (None,                                 20),    # no manuscript
                (MANUSCRIPTS['no-reviews'],            20),    # no reviews
                (MANUSCRIPTS['no-preprint-doi'],       20),    # no preprint DOI
            ]
        ]
        for parsed_file in fixtures:
            with self.subTest(parsed_file=parsed_file):
                parsed_files = [parsed_file] + self.parsed_files
                with self.assertRaises(ValueError):
                    deposit(parsed_files, self.db, dry_run=False)
                deposit_file_mock.assert_not_called()
