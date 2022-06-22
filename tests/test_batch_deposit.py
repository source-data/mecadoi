from glob import glob
from os import listdir, mkdir
from typing import Any, List, Tuple
from unittest.mock import Mock, patch
import responses
from shutil import copy, rmtree

from yaml import safe_load
from src.batch import batch_deposit, BatchDepositRun
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

        self.input_files = [
            'no-article',
            'no-author-reply',
            'no-manifest',
            'no-preprint-doi',
            'no-reviews',
            'multiple-revision-rounds',
            'single-revision-round',
        ]
        self.setup_input_directory(self.input_files)

        self.expected_output = BatchDepositRun(
            timestamp=PUBLICATION_DATE,
            invalid=[
                f'{self.input_directory}/no-article.zip',
                f'{self.input_directory}/no-manifest.zip',
            ],
            incomplete=[
                f'{self.input_directory}/no-reviews.zip',
                f'{self.input_directory}/no-preprint-doi.zip',
            ],
            processed=[
                f'{self.input_directory}/no-author-reply.zip',
                f'{self.input_directory}/multiple-revision-rounds.zip',
                f'{self.input_directory}/single-revision-round.zip',
            ],
        )
        self.expected_deposition_files = [
            ('no-author-reply', '10.1101/no-author-reply.123.456.7890/deposition.xml'),
            ('multiple-revision-rounds', '10.1101/multiple-revision-rounds.123.456.7890/deposition.xml'),
            ('single-revision-round', '10.1101/single-revision-round.123.456.7890/deposition.xml'),
        ]
        self.expected_export_files = [
            'no-author-reply',
            'multiple-revision-rounds',
            'single-revision-round',
        ]

        self.expected_response = '<html><head><title>SUCCESS</title></head><body><h2>SUCCESS</h2></body></html>'
        responses.add(responses.POST, CROSSREF_DEPOSITION_URL, body=self.expected_response, status=200)
        return super().setUp()

    @responses.activate
    def test_batch_generate(self, datetime_mock: Mock, get_free_doi_mock: Mock) -> None:
        actual_output = self.do_batch_generate()

        self.assert_results_equal(self.expected_output, actual_output)
        self.assert_deposition_files_in_output_dir(self.expected_deposition_files)
        self.assert_export_files_in_output_dir(self.expected_export_files)

    @responses.activate
    def test_batch_generate_same_file(self, datetime_mock: Mock, get_free_doi_mock: Mock) -> None:
        expected_output_second_run = BatchDepositRun(
            timestamp=PUBLICATION_DATE,
            invalid=self.expected_output.invalid,
            incomplete=self.expected_output.incomplete,
            duplicate=self.expected_output.processed,
            processed=[],
        )

        # do the first batch run
        self.do_batch_generate()

        # Setup the input directory again since the input MECAs are deleted after each run
        self.setup_input_directory(self.input_files)
        result_second_run = self.do_batch_generate()

        self.assert_results_equal(expected_output_second_run, result_second_run)
        self.assert_deposition_files_in_output_dir(self.expected_deposition_files)
        self.assert_export_files_in_output_dir(self.expected_export_files)

    def assert_results_equal(self, expected: BatchDepositRun, actual: BatchDepositRun) -> None:
        self.assertEqual(expected, actual)

    def setup_input_directory(self, files: List[str]) -> None:
        try:
            rmtree(self.input_directory)
        except FileNotFoundError:
            pass
        mkdir(self.input_directory)

        for file in [self.get_meca_archive_path(filename) for filename in files]:
            copy(file, self.input_directory)

        self.assert_num_files_in_dir(self.input_directory, len(files))

    def do_batch_generate(self) -> BatchDepositRun:
        return batch_deposit(self.input_directory, self.output_directory)

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
