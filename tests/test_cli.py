from dataclasses import asdict
from datetime import datetime
from os import mkdir, remove
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
from src.config import DB_URL
from src.crossref.verify import VerificationResult
from src.db import DepositionAttempt, ParsedFile
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
        self.assertEqual(self.get_db_url(), DB_URL)
        try:
            rmtree(self.output_directory)
        except FileNotFoundError:
            pass
        mkdir(self.output_directory)

        super().setUp()

    def get_db_file(self) -> str:
        return f"{self.output_directory}/batch.sqlite3"

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


OutputDirName = "deadbeef-2708-4afb-bbde-5890bd7e8fd0"


@patch("src.cli.batch.commands.uuid4", return_value=OutputDirName)
class ParseTestCase(BaseBatchTestCase, BaseParseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.input_directory = self.MECA_TARGET_DIR
        self.expected_parsed_files = [
            ParsedFile(
                path=parsed_file.path.replace(
                    f"{self.MECA_TARGET_DIR}",
                    f"{self.output_directory}/parsed/{OutputDirName}",
                ),
                received_at=parsed_file.received_at,
                manuscript=parsed_file.manuscript,
                doi=parsed_file.doi,
                status=parsed_file.status,
            )
            for parsed_file in self.expected_parsed_files
        ]

    def test_batch_parse(self, _uuid_mock: Mock) -> None:
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

    def test_batch_deposit_retry(
        self,
        _verify: Mock,
        _get_random_doi: Mock,
        _get_free_doi: Mock,
        deposit_file_mock: Mock,
    ) -> None:
        initial_deposition_attempts = [
            DepositionAttempt(
                meca=self.parsed_files[0],
                deposition=Path("tests/resources/expected/multiple-revision-rounds.xml").read_text(),
                attempted_at=datetime.now(),
                status=DepositionAttempt.Failed,
            ),
            DepositionAttempt(
                meca=self.parsed_files[1],
                deposition=Path("tests/resources/expected/no-author-reply.xml").read_text(),
                attempted_at=datetime.now(),
                status=DepositionAttempt.VerificationFailed,
            ),
        ]
        self.db.insert_all(initial_deposition_attempts)

        result = self.run_mecadoi_command(
            ["batch", "deposit", "-o", self.output_directory, "--retry-failed", "--no-dry-run"]
        )
        self.assertEqual(0, result.exit_code)

        self.expected_deposition_attempts = lambda *_args, **_kwargs: [
            DepositionAttempt(
                meca=self.parsed_files[0],
                deposition=Path("tests/resources/expected/multiple-revision-rounds.xml").read_text(),
                attempted_at=datetime.now(),
                status=DepositionAttempt.Succeeded,
            ),
            DepositionAttempt(
                meca=self.parsed_files[1],
                deposition=Path("tests/resources/expected/no-author-reply.xml").read_text(),
                attempted_at=datetime.now(),
                status=DepositionAttempt.Succeeded,
            ),
        ]

        expected_output = self.expected_output(dry_run=False)
        actual_output = self.assert_cli_output_equal(expected_output, result, ["id"])

        self.assert_deposition_attempts_in_db(initial_deposition_attempts + self.expected_deposition_attempts())
        self.assert_articles_in_output_dir(actual_output["id"], self.expected_articles[:2])
        self.assertEqual(2, len(deposit_file_mock.mock_calls))

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


class PruneTestCase(BaseBatchTestCase):

    def path(self, filename: str) -> Path:
        return Path(self.output_directory) / filename

    def assert_files_exist(self, filenames: List[str]) -> None:
        for filename in filenames:
            self.assertTrue(self.path(filename).exists())

    def assert_files_do_not_exist(self, filenames: List[str]) -> None:
        for filename in filenames:
            self.assertFalse(self.path(filename).exists())

    def setUp(self) -> None:
        super().setUp()
        self.existing_files = [
            "exists.zip",
            "yes.zml",
        ]
        self.already_pruned_files = [
            "no.txt",
            "pruned.zip",
        ]
        for filename in self.existing_files:
            self.path(filename).write_text("this file is present")
        self.db.insert_all([
            ParsedFile(path=str(self.path(filename)), received_at=datetime.now())
            for filename in self.existing_files + self.already_pruned_files
        ])

    def test_prune_files(self):
        self.assert_files_exist(self.existing_files)
        self.assert_files_do_not_exist(self.already_pruned_files)

        result = self.run_mecadoi_command(
            ["batch", "prune", "--no-dry-run"]
        )
        self.assertEqual(0, result.exit_code)

        expected_output = {
            "deleted": [str(self.path(filename)) for filename in self.existing_files],
            "dry_run": False,
        }
        self.assert_cli_output_equal(expected_output, result, [])

        self.assert_files_do_not_exist(self.already_pruned_files + self.existing_files)

    @patch("src.cli.batch.commands.remove", side_effect=ValueError("failed"))
    def test_prune_files_fails(self, _remove_mock: Mock):
        self.assert_files_exist(self.existing_files)
        self.assert_files_do_not_exist(self.already_pruned_files)

        result = self.run_mecadoi_command(
            ["batch", "prune", "--no-dry-run"]
        )
        self.assertEqual(0, result.exit_code)

        expected_output = {
            "dry_run": False,
            "failed": [
                str(self.path(filename))
                for filename in self.existing_files
            ],
        }
        self.assert_cli_output_equal(expected_output, result, [])

    def test_prune_files_dry_run(self) -> None:
        self.assert_files_exist(self.existing_files)
        self.assert_files_do_not_exist(self.already_pruned_files)

        result = self.run_mecadoi_command(
            ["batch", "prune"]
        )
        self.assertEqual(0, result.exit_code)

        expected_output = {
            "deleted": [str(self.path(filename)) for filename in self.existing_files],
            "dry_run": True,
        }
        self.assert_cli_output_equal(expected_output, result, [])

        self.assert_files_exist(self.existing_files)
        self.assert_files_do_not_exist(self.already_pruned_files)
