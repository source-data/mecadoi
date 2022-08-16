from dataclasses import asdict
from os import mkdir, walk
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, List
from unittest.mock import Mock, patch
from click.testing import CliRunner, Result
from yaml import Loader, load, safe_load
from src.article import Article
from src.cli.batch.commands import (
    group_deposition_attempts_by_status,
    group_parsed_files_by_status,
)
from src.cli.main import main as mecadoi
from src.crossref.verify import VerificationResult
from tests.common import MecaArchiveTestCase
from tests.test_article import DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES
from tests.test_batch import BaseDepositTestCase, BaseParseTestCase
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
        test_file = self.get_meca_archive_path("multiple-revision-rounds")
        title = "An article with multiple revision rounds."
        doi = "10.12345/multiple-revision-rounds.1234567890"
        preprint_doi = "10.1101/multiple-revision-rounds.123.456.7890"
        publisher = "Review Commons - TEST"
        result = self.run_mecadoi_command(["meca", "info", test_file])
        self.assertEqual(0, result.exit_code)
        self.assertIn(title, result.output)
        self.assertIn(doi, result.output)
        self.assertIn(preprint_doi, result.output)
        self.assertIn(publisher, result.output)


class BaseBatchTestCase(CliTestCase, BatchDbTestCase):
    def setUp(self) -> None:
        self.output_directory = "tests/tmp/batch"
        try:
            rmtree(self.output_directory)
        except FileNotFoundError:
            pass
        mkdir(self.output_directory)

        self.db_file = f"{self.output_directory}/batch.sqlite3"
        super().setUp()

    def assert_cli_output_equal(
        self,
        expected: Dict[str, Any],
        result: Result,
        attrs_to_ignore: List[str],
    ) -> Any:
        actual_output = load(result.output, Loader=Loader)
        for attr_to_ignore in attrs_to_ignore:
            self.assertIsNotNone(actual_output[attr_to_ignore])
            expected[attr_to_ignore] = actual_output[attr_to_ignore]
        self.assertEqual(expected, actual_output)
        return actual_output


class ParseTestCase(BaseBatchTestCase, BaseParseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.input_directory = self.MECA_TARGET_DIR
        self.input_directory_structure = list(walk(self.input_directory))

    def test_batch_parse(self) -> None:
        """
        Verifies that all files in the input directory are parsed, entered into the database, and moved to the output
        directory.
        """
        result = self.run_mecadoi_command(
            ["batch", "parse", "-o", self.output_directory, self.input_directory]
        )
        self.assertEqual(0, result.exit_code)
        expected_output = group_parsed_files_by_status(self.expected_parsed_files)
        actual_output = self.assert_cli_output_equal(expected_output, result, ["id"])

        self.assert_parsed_files_in_db(self.expected_parsed_files)
        self.assert_input_files_are_in_output_dir(actual_output)

    def assert_input_files_are_in_output_dir(self, actual: Dict[str, Any]) -> None:
        expected_output_dir = f'{self.output_directory}/parsed/{actual["id"]}'
        files_in_output_dir = [
            path for path in Path(expected_output_dir).glob("**/*") if path.is_file()
        ]
        self.assertEqual(len(self.input_files), len(files_in_output_dir))


@patch("src.batch.deposit_file")
@patch(
    "src.batch.verify",
    return_value=[
        VerificationResult(
            preprint_doi="preprint_doi",
            all_reviews_present=True,
            author_reply_matches=True,
        )
    ],
)
@patch("src.batch.get_random_doi", return_value=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES)
@patch("src.batch.get_free_doi", return_value=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES)
class DepositTestCase(BaseBatchTestCase, BaseDepositTestCase):
    def test_batch_deposit_dry_run(
        self,
        _verify: Mock,
        _get_random_doi: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        result = self.run_mecadoi_command(
            ["batch", "deposit", "-o", self.output_directory, "--dry-run"]
        )
        self.assertEqual(0, result.exit_code)

        expected_output = self.expected_output(dry_run=True)
        actual_output = self.assert_cli_output_equal(expected_output, result, ["id"])

        self.assert_deposition_attempts_in_db([])
        self.assert_articles_in_output_dir(actual_output["id"], [])
        deposit_file_mock.assert_not_called()

    def test_batch_deposit(
        self,
        _verify: Mock,
        _get_random_doi: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        result = self.run_mecadoi_command(
            ["batch", "deposit", "-o", self.output_directory, "--no-dry-run"]
        )
        self.assertEqual(0, result.exit_code)

        expected_output = self.expected_output(dry_run=False)
        actual_output = self.assert_cli_output_equal(expected_output, result, ["id"])

        self.assert_deposition_attempts_in_db(self.expected_deposition_attempts())
        self.assert_articles_in_output_dir(actual_output["id"], self.expected_articles)
        self.assertEqual(3, len(deposit_file_mock.mock_calls))

    def assert_articles_in_output_dir(
        self, id_batch_run: str, expected_articles: List[Article]
    ) -> None:
        output_file = f"{self.output_directory}/deposited/{id_batch_run}.yml"
        if not expected_articles:
            self.assertFalse(Path(output_file).exists())
            return

        expected_content = [asdict(article) for article in expected_articles]

        with open(output_file, "r") as f:
            actual_content = safe_load(f)

        self.assertEqual(expected_content, actual_content)

    def expected_output(self, dry_run: bool = False) -> Dict[str, Any]:
        expected_deposition_attempts = self.expected_deposition_attempts(
            dry_run=dry_run
        )
        expected_output = group_deposition_attempts_by_status(
            expected_deposition_attempts, dry_run=dry_run
        )
        expected_output["dry_run"] = dry_run
        return expected_output
