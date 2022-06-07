from datetime import datetime
from glob import glob
from os import listdir, mkdir
from pathlib import Path
from typing import List
from unittest import TestCase
import responses
from shutil import copy, rmtree
from src.batch import batch_deposit, BatchDepositRun, DepositionResult, MecaDeposition, MecaParsingResult
from src.config import CROSSREF_DEPOSITION_URL


class TestBatchDeposit(TestCase):

    def setUp(self) -> None:
        self.base_dir = 'tests/tmp/batch'
        try:
            rmtree(self.base_dir)
        except FileNotFoundError:
            pass
        mkdir(self.base_dir)

        self.maxDiff = None

        self.expected_response = '<html><head><title>SUCCESS</title></head><body><h2>SUCCESS</h2></body></html>'
        responses.add(responses.POST, CROSSREF_DEPOSITION_URL, body=self.expected_response, status=200)

        return super().setUp()

    @responses.activate
    def test_batch_deposit(self) -> None:
        input_files = [
            'multiple-revision-rounds.zip',
            'no-preprint-doi.zip',
            'no-reviews.zip',
        ]
        expected_output = BatchDepositRun(
            results=[
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input='tests/tmp/batch/input/multiple-revision-rounds.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=False,
                    ),
                    deposition_file_generation=DepositionResult(
                        output='tests/tmp/batch/output/10.1101/2022.02.15.480564/deposition.xml',
                        error=None,
                    ),
                ),
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input='tests/tmp/batch/input/no-preprint-doi.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=False,
                        doi_already_processed=None,
                    )
                ),
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input='tests/tmp/batch/input/no-reviews.zip',
                        error=None,
                        has_reviews=False,
                        has_preprint_doi=False,
                        doi_already_processed=None,
                    )
                ),
            ],
            timestamp=datetime.now(),
        )

        input_directory = f'{self.base_dir}/input'
        self.setup_input_directory(input_directory, input_files)

        output_directory = f'{self.base_dir}/output'
        result = self.do_batch_deposit(input_directory, output_directory)
        self.assert_results_equal(expected_output, result)

        num_files_in_input_directory = len(glob(f'{input_directory}/*'))
        self.assertEqual(0, num_files_in_input_directory)

        expected_deposition_file = 'tests/tmp/batch/output/10.1101/2022.02.15.480564/deposition.xml'
        self.assertTrue(Path(expected_deposition_file).exists())

        files_in_archive = [Path(file).name for file in glob(f'{output_directory}/archive/**/*')]
        self.assertListEqual(sorted(input_files), sorted(files_in_archive))

    @responses.activate
    def test_batch_deposit_same_file(self) -> None:
        input_files = [
            'multiple-revision-rounds.zip',
        ]
        expected_output_first_run = BatchDepositRun(
            results=[
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input='tests/tmp/batch/input/multiple-revision-rounds.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=False,
                    ),
                    deposition_file_generation=DepositionResult(
                        output='tests/tmp/batch/output/10.1101/2022.02.15.480564/deposition.xml',
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
                        input='tests/tmp/batch/input/multiple-revision-rounds.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=True,
                    ),
                ),
            ],
            timestamp=datetime.now(),
        )

        input_directory = f'{self.base_dir}/input'
        self.setup_input_directory(input_directory, input_files)

        output_directory = f'{self.base_dir}/output'
        result_first_run = self.do_batch_deposit(input_directory, output_directory)
        self.assert_results_equal(expected_output_first_run, result_first_run)

        # Setup the input directory again since the MECAs are archived after each run
        self.setup_input_directory(input_directory, input_files)
        result_second_run = self.do_batch_deposit(input_directory, output_directory)
        self.assert_results_equal(expected_output_second_run, result_second_run)

    def assert_results_equal(self, expected: BatchDepositRun, actual: BatchDepositRun) -> None:
        self.assertCountEqual(expected.results, actual.results)

    def setup_input_directory(self, input_dir: str, files: List[str]) -> None:
        try:
            rmtree(input_dir)
        except FileNotFoundError:
            pass
        mkdir(input_dir)
        num_files_in_input_dir = len(listdir(input_dir))
        self.assertEqual(0, num_files_in_input_dir)

        for file in [f'tests/resources/meca/{filename}' for filename in files]:
            copy(file, input_dir)

        num_files_in_input_dir = len(listdir(input_dir))
        self.assertEqual(len(files), num_files_in_input_dir)

    def do_batch_deposit(self, input_directory: str, output_directory: str) -> BatchDepositRun:
        return batch_deposit(input_directory, output_directory, verbose=False)