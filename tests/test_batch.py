from datetime import datetime, timedelta
from enum import Enum, auto
from typing import List

from src.batch import parse, ParsedFiles
from src.db import ParsedFile
from tests.common import MecaArchiveTestCase
from tests.test_db import BatchDbTestCase
from tests.test_meca import MANUSCRIPTS


class ParsedFileStatus(Enum):
    INVALID = auto()
    NO_REVIEWS = auto()
    NO_PREPRINT_DOI = auto()
    READY_FOR_DEPOSITION = auto()


class BatchTestCase(MecaArchiveTestCase, BatchDbTestCase):

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
        meca_archives_in_db = self.db.get_all_parsed_files()

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

    def assert_timestamps_within_interval(self, expected: datetime, actual: datetime, interval: timedelta) -> None:
        delta = actual - expected
        self.assertGreaterEqual(interval, delta)


class ParseTestCase(BatchTestCase):

    def test_batch_parse(self) -> None:
        """Verifies that all given files are parsed and entered into the database."""
        actual_output = parse(self.input_files, self.db)

        self.assert_results_equal(self.expected_output, actual_output)
        self.assert_meca_archives_in_db(self.expected_db_contents)
