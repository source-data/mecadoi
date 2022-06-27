from dataclasses import asdict
from os import mkdir, walk
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, List
from click.testing import CliRunner, Result
from yaml import Loader, load
from src.cli.main import main as mecadoi
from tests.common import MecaArchiveTestCase
from tests.test_batch import BatchTestCase
from tests.test_db import BatchDbTestCase


class CliTestCase(MecaArchiveTestCase):

    def setUp(self) -> None:
        self.runner = CliRunner()
        self.maxDiff = None
        return super().setUp()

    def run_mecadoi_command(self, command: List[str]) -> Result:
        return self.runner.invoke(mecadoi, command)


class MecaTestCase(CliTestCase):
    def test_meca_info(self) -> None:
        test_file = self.get_meca_archive_path('multiple-revision-rounds')
        title = 'An article with multiple revision rounds.'
        doi = '10.12345/multiple-revision-rounds.1234567890'
        preprint_doi = '10.1101/multiple-revision-rounds.123.456.7890'
        publisher = 'Review Commons - TEST'
        result = self.run_mecadoi_command(['meca', 'info', test_file])
        self.assertEqual(0, result.exit_code)
        self.assertIn(title, result.output)
        self.assertIn(doi, result.output)
        self.assertIn(preprint_doi, result.output)
        self.assertIn(publisher, result.output)


class BatchParseTestCase(CliTestCase, BatchTestCase, BatchDbTestCase):

    def setUp(self) -> None:
        self.output_directory = 'tests/tmp/batch'
        try:
            rmtree(self.output_directory)
        except FileNotFoundError:
            pass
        mkdir(self.output_directory)

        self.db_file = f'{self.output_directory}/batch.sqlite3'
        super().setUp()

        self.input_directory = self.MECA_TARGET_DIR
        self.input_directory_structure = list(walk(self.input_directory))

    def test_batch_parse(self) -> None:
        """
        Verifies that all files in the input directory are parsed, entered into the database, and moved to the output
        directory.
        """
        result = self.run_mecadoi_command(['batch', 'parse', '-o', self.output_directory, self.input_directory])
        self.assertEqual(0, result.exit_code)

        actual_output = load(result.output, Loader=Loader)
        expected_output = asdict(self.expected_output)
        self.assert_cli_output_equal(expected_output, actual_output)

        self.assert_meca_archives_in_db(self.expected_db_contents)
        self.assert_input_files_are_in_output_dir(actual_output)

    def assert_cli_output_equal(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> None:
        self.assertIsNotNone(actual['id'])
        expected['id'] = actual['id']
        self.assertEqual(expected, actual)

    def assert_input_files_are_in_output_dir(self, actual: Dict[str, Any]) -> None:
        expected_output_dir = f'{self.output_directory}/{actual["id"]}'
        files_in_output_dir = [path for path in Path(expected_output_dir).glob('**/*') if path.is_file()]
        self.assertEqual(len(self.input_files), len(files_in_output_dir))
