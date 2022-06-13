from datetime import datetime
from glob import glob
from os import listdir, mkdir
from pathlib import Path
from typing import List
import responses
from shutil import copy, rmtree
from src.batch import (
    batch_generate,
    BatchGenerateRun,
    DepositionResult,
    DepositionFileGenerationResult,
    MecaParsingResult,
)
from tests.common import MecaArchiveTestCase


class TestBatchDeposit(MecaArchiveTestCase):

    def setUp(self) -> None:
        self.base_dir = 'tests/tmp/batch'
        try:
            rmtree(self.base_dir)
        except FileNotFoundError:
            pass
        mkdir(self.base_dir)

        self.maxDiff = None

        return super().setUp()

    @responses.activate
    def test_batch_generate(self) -> None:
        input_files = [
            'multiple-revision-rounds.zip',
            'no-preprint-doi.zip',
            'no-reviews.zip',
        ]
        expected_output = BatchGenerateRun(
            results=[
                DepositionFileGenerationResult(
                    meca_parsing=MecaParsingResult(
                        input='tests/tmp/batch/input/multiple-revision-rounds.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=False,
                    ),
                    deposition_file_generation=DepositionResult(
                        output='tests/tmp/batch/output/10.1101/multiple-revision-rounds.123.456.7890/deposition.xml',
                        error=None,
                    ),
                ),
                DepositionFileGenerationResult(
                    meca_parsing=MecaParsingResult(
                        input='tests/tmp/batch/input/no-preprint-doi.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=False,
                        doi_already_processed=None,
                    )
                ),
                DepositionFileGenerationResult(
                    meca_parsing=MecaParsingResult(
                        input='tests/tmp/batch/input/no-reviews.zip',
                        error=None,
                        has_reviews=False,
                        has_preprint_doi=True,
                        doi_already_processed=None,
                    )
                ),
            ],
            timestamp=datetime.now(),
        )

        input_directory = f'{self.base_dir}/input'
        self.setup_input_directory(input_directory, input_files)

        output_directory = f'{self.base_dir}/output'
        result = self.do_batch_generate(input_directory, output_directory)
        self.assert_results_equal(expected_output, result)

        num_files_in_input_directory = len(glob(f'{input_directory}/*'))
        self.assertEqual(0, num_files_in_input_directory)

        expected_deposition_file = 'tests/tmp/batch/output/10.1101/multiple-revision-rounds.123.456.7890/deposition.xml'
        self.assertTrue(Path(expected_deposition_file).exists())

    @responses.activate
    def test_batch_generate_same_file(self) -> None:
        input_files = [
            'multiple-revision-rounds.zip',
        ]
        expected_output_first_run = BatchGenerateRun(
            results=[
                DepositionFileGenerationResult(
                    meca_parsing=MecaParsingResult(
                        input='tests/tmp/batch/input/multiple-revision-rounds.zip',
                        error=None,
                        has_reviews=True,
                        has_preprint_doi=True,
                        doi_already_processed=False,
                    ),
                    deposition_file_generation=DepositionResult(
                        output='tests/tmp/batch/output/10.1101/multiple-revision-rounds.123.456.7890/deposition.xml',
                        error=None,
                    ),
                ),
            ],
            timestamp=datetime.now(),
        )
        expected_output_second_run = BatchGenerateRun(
            results=[
                DepositionFileGenerationResult(
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
        result_first_run = self.do_batch_generate(input_directory, output_directory)
        self.assert_results_equal(expected_output_first_run, result_first_run)

        # Setup the input directory again since the input MECAs are deleted after each run
        self.setup_input_directory(input_directory, input_files)
        result_second_run = self.do_batch_generate(input_directory, output_directory)
        self.assert_results_equal(expected_output_second_run, result_second_run)

    def assert_results_equal(self, expected: BatchGenerateRun, actual: BatchGenerateRun) -> None:
        self.assertCountEqual(expected.results, actual.results)

    def setup_input_directory(self, input_dir: str, files: List[str]) -> None:
        try:
            rmtree(input_dir)
        except FileNotFoundError:
            pass
        mkdir(input_dir)
        num_files_in_input_dir = len(listdir(input_dir))
        self.assertEqual(0, num_files_in_input_dir)

        for file in [f'{self.MECA_TARGET_DIR}/{filename}' for filename in files]:
            copy(file, input_dir)

        num_files_in_input_dir = len(listdir(input_dir))
        self.assertEqual(len(files), num_files_in_input_dir)

    def do_batch_generate(self, input_directory: str, output_directory: str) -> BatchGenerateRun:
        return batch_generate(input_directory, output_directory, verbose=False)
