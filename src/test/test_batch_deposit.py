from os import listdir, mkdir
import responses
from shutil import copy, rmtree

import yaml
from src.batch import batch_deposit, BatchDepositRun
from src.batch.batch import DepositionResult, MecaDeposition, MecaParsingResult
from src.crossref.api import CROSSREF_DEPOSITION_URL
from .common import DoiDbTestCase


class TestBatchDeposit(DoiDbTestCase):

    def setUp(self) -> None:
        self.base_dir = 'src/test/tmp/batch'
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
    def test_batch_deposit(self):
        input_files = [
            'mutagenesis.zip',
            'no-preprint-doi.zip',
            'no-reviews.zip',
        ]
        expected_output = BatchDepositRun(
            results=[
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input='src/test/tmp/batch/input/mutagenesis.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=False,
                    ),
                    depositition_file_generation=DepositionResult(
                        output='src/test/tmp/batch/output/10.1101/2022.02.15.480564/deposition.xml',
                        error=None,
                    ),
                ),
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input='src/test/tmp/batch/input/no-reviews.zip',
                        error=None,
                        has_reviews=False,
                        has_preprint_doi=False,
                        doi_already_processed=None,
                    )
                ),
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input='src/test/tmp/batch/input/no-preprint-doi.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=False,
                        doi_already_processed=None,
                    )
                ),
            ],
            timestamp=None,
        )

        input_directory = f'{self.base_dir}/input'
        self.setup_input_directory(input_directory, input_files)

        output_directory = f'{self.base_dir}/output'
        result = self.do_batch_deposit(input_directory, output_directory)
        self.assert_results_equal(expected_output, result)

    @responses.activate
    def test_batch_deposit_same_file(self):
        input_files = [
            'mutagenesis.zip',
        ]
        expected_output_first_run = BatchDepositRun(
            results=[
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input='src/test/tmp/batch/input/mutagenesis.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=False,
                    ),
                    depositition_file_generation=DepositionResult(
                        output='src/test/tmp/batch/output/10.1101/2022.02.15.480564/deposition.xml',
                        error=None,
                    ),
                ),
            ],
            timestamp=None,
        )
        expected_output_second_run = BatchDepositRun(
            results=[
                MecaDeposition(
                    meca_parsing=MecaParsingResult(
                        input='src/test/tmp/batch/input/mutagenesis.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=True,
                    ),
                ),
            ],
            timestamp=None,
        )

        input_directory = f'{self.base_dir}/input'
        self.setup_input_directory(input_directory, input_files)

        output_directory = f'{self.base_dir}/output'
        result_first_run = self.do_batch_deposit(input_directory, output_directory)
        self.assert_results_equal(expected_output_first_run, result_first_run)

        result_second_run = self.do_batch_deposit(input_directory, output_directory)
        self.assert_results_equal(expected_output_second_run, result_second_run)

    def assert_results_equal(self, expected, actual):
        expected.timestamp = actual.timestamp
        self.assertEqual(yaml.dump(expected), yaml.dump(actual))

    def setup_input_directory(self, input_dir, files):
        mkdir(input_dir)
        num_files_in_input_dir = len(listdir(input_dir))
        self.assertEqual(0, num_files_in_input_dir)

        for file in [f'src/test/test_data/{filename}' for filename in files]:
            copy(file, input_dir)

        num_files_in_input_dir = len(listdir(input_dir))
        self.assertEqual(len(files), num_files_in_input_dir)

    def do_batch_deposit(self, input_directory, output_directory):
        return batch_deposit(
            input_directory,
            output_directory,
            verbose=False,
            strict_validation=False,
        )