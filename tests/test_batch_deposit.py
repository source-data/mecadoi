from datetime import datetime
from glob import glob
from os import listdir, mkdir
from typing import Any, List, Tuple
from unittest.mock import Mock, patch
import responses
from shutil import copy, rmtree

from yaml import safe_load
from src.batch import (
    batch_deposit,
    BatchDepositRun,
    DepositionResult,
    MecaDeposition,
    MecaParsingResult,
)
from src.config import CROSSREF_DEPOSITION_URL
from tests.common import DepositionFileTestCase, MecaArchiveTestCase
from tests.test_article import DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES, PUBLICATION_DATE


@patch('src.batch.get_free_doi', return_value=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES)
@patch('src.batch.datetime', **{'now.return_value': PUBLICATION_DATE})  # type: ignore[call-overload]
class TestBatchDeposit(MecaArchiveTestCase, DepositionFileTestCase):

    def setUp(self) -> None:
        self.base_dir = 'tests/tmp/batch'
        try:
            rmtree(self.base_dir)
        except FileNotFoundError:
            pass
        mkdir(self.base_dir)

        self.input_directory = f'{self.base_dir}/input'
        self.output_directory = f'{self.base_dir}/output'

        self.maxDiff = None

        self.expected_response = '<html><head><title>SUCCESS</title></head><body><h2>SUCCESS</h2></body></html>'
        responses.add(responses.POST, CROSSREF_DEPOSITION_URL, body=self.expected_response, status=200)

        return super().setUp()

    @responses.activate
    def test_batch_deposit(self, datetime_mock: Mock, get_free_doi_mock: Mock) -> None:
        input_files = [
            'multiple-revision-rounds',
            'single-revision-round',
            'no-preprint-doi',
            'no-reviews',
        ]
        self.setup_input_directory(input_files)
        expected_output = BatchDepositRun(
            results=[
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input=f'{self.input_directory}/multiple-revision-rounds.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=False,
                    ),
                    deposition_file_generation=DepositionResult(
                        output=f'{self.output_directory}/10.1101/multiple-revision-rounds.123.456.7890/deposition.xml',
                        error=None,
                    ),
                    crossref_deposition=DepositionResult(
                        output=self.expected_response,
                        error=None,
                    ),
                ),
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input=f'{self.input_directory}/single-revision-round.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=False,
                    ),
                    deposition_file_generation=DepositionResult(
                        output=f'{self.output_directory}/10.1101/single-revision-round.123.456.7890/deposition.xml',
                        error=None,
                    ),
                    crossref_deposition=DepositionResult(
                        output=self.expected_response,
                        error=None,
                    ),
                ),
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input=f'{self.input_directory}/no-preprint-doi.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=False,
                        doi_already_processed=None,
                    )
                ),
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input=f'{self.input_directory}/no-reviews.zip',
                        error=None,
                        has_reviews=False,
                        has_preprint_doi=True,
                        doi_already_processed=None,
                    )
                ),
            ],
            timestamp=datetime.now(),
        )

        actual_output = self.do_batch_deposit()
        self.assert_results_equal(expected_output, actual_output)

        self.assert_input_dir_is_empty()

        expected_deposition_files = [
            ('multiple-revision-rounds', '10.1101/multiple-revision-rounds.123.456.7890/deposition.xml'),
            ('single-revision-round', '10.1101/single-revision-round.123.456.7890/deposition.xml'),
        ]
        self.assert_deposition_files_in_output_dir(expected_deposition_files)

        expected_export_files = [
            'multiple-revision-rounds',
            'single-revision-round',
        ]
        self.assert_export_files_in_output_dir(expected_export_files)

    @responses.activate
    def test_batch_deposit_same_file(self, datetime_mock: Mock, get_free_doi_mock: Mock) -> None:
        input_files = [
            'multiple-revision-rounds',
        ]
        expected_output_first_run = BatchDepositRun(
            results=[
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input=f'{self.input_directory}/multiple-revision-rounds.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=False,
                    ),
                    deposition_file_generation=DepositionResult(
                        output=f'{self.output_directory}/10.1101/multiple-revision-rounds.123.456.7890/deposition.xml',
                        error=None,
                    ),
                    crossref_deposition=DepositionResult(
                        output=self.expected_response,
                        error=None,
                    ),
                ),
            ],
            timestamp=datetime.now(),
        )
        expected_output_second_run = BatchDepositRun(
            results=[
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input=f'{self.input_directory}/multiple-revision-rounds.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=True,
                    ),
                ),
            ],
            timestamp=datetime.now(),
        )

        self.setup_input_directory(input_files)

        result_first_run = self.do_batch_deposit()
        self.assert_results_equal(expected_output_first_run, result_first_run)

        expected_deposition_files = [
            ('multiple-revision-rounds', '10.1101/multiple-revision-rounds.123.456.7890/deposition.xml'),
        ]
        self.assert_deposition_files_in_output_dir(expected_deposition_files)

        expected_export_files = ['multiple-revision-rounds']
        self.assert_export_files_in_output_dir(expected_export_files)

        # Setup the input directory again since the input MECAs are deleted after each run
        self.setup_input_directory(input_files)
        result_second_run = self.do_batch_deposit()

        self.assert_results_equal(expected_output_second_run, result_second_run)
        self.assert_deposition_files_in_output_dir(expected_deposition_files)
        self.assert_export_files_in_output_dir(expected_export_files)

    def assert_results_equal(self, expected: BatchDepositRun, actual: BatchDepositRun) -> None:
        def sorted_results(items: List[MecaDeposition]) -> List[MecaDeposition]:
            return sorted(items, key=lambda i: i.meca_parsing.input)
        self.assertEqual(sorted_results(expected.results), sorted_results(actual.results))

    def setup_input_directory(self, files: List[str]) -> None:
        try:
            rmtree(self.input_directory)
        except FileNotFoundError:
            pass
        mkdir(self.input_directory)
        self.assert_input_dir_is_empty()

        for file in [self.get_meca_archive_path(filename) for filename in files]:
            copy(file, self.input_directory)

        self.assert_num_files_in_dir(self.input_directory, len(files))

    def do_batch_deposit(self) -> BatchDepositRun:
        return batch_deposit(self.input_directory, self.output_directory, verbose=False, dry_run=False)

    def assert_input_dir_is_empty(self) -> None:
        self.assert_num_files_in_dir(self.input_directory, 0)

    def assert_num_files_in_dir(self, dir: str, expected_num_files_in_dir: int) -> None:
        actual_num_files_in_dir = len(listdir(dir))
        self.assertEqual(expected_num_files_in_dir, actual_num_files_in_dir)

    def assert_deposition_files_in_output_dir(self, expected_files: List[Tuple[str, str]]) -> None:
        # find all .xml files (i.e. deposition files) in the output directory
        files_in_output_directory = list(glob(f'{self.output_directory}/**/*.xml', recursive=True))

        # verify we have the right amount of deposition files
        self.assertEqual(len(expected_files), len(files_in_output_directory))

        # check that all deposition files in the output directory have the expected content
        for deposition_file_name, deposition_file_path_in_output_dir in expected_files:
            deposition_file_path = f'{self.output_directory}/{deposition_file_path_in_output_dir}'
            self.assertIn(deposition_file_path, files_in_output_directory)

            expected_deposition_file_path = f'tests/resources/expected/{deposition_file_name}.xml'
            self.assertDepositionFileEquals(expected_deposition_file_path, deposition_file_path)

    def assert_export_files_in_output_dir(self, expected_files: List[str]) -> None:
        # find the .yml file (i.e. the export file) in the output directory
        files_in_output_directory = list(glob(f'{self.output_directory}/**/*.yml', recursive=True))

        # verify we have only one export file
        self.assertEqual(1, len(files_in_output_directory))

        def load_yaml(file_name: str) -> Any:
            with open(file_name) as f:
                return safe_load(f)

        actual_exported_data = load_yaml(files_in_output_directory[0])
        expected_exported_data = [
            load_yaml(f'tests/resources/expected/{file_name}.yml') for file_name in expected_files
        ]
        self.assertEqual(expected_exported_data, actual_exported_data)
