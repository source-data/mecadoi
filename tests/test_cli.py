from typing import List
from click.testing import CliRunner, Result
from src.cli.main import main as mecadoi
from tests.common import MecaArchiveTestCase


class CliTestCase(MecaArchiveTestCase):

    def setUp(self) -> None:
        self.runner = CliRunner()
        return super().setUp()

    def run_mecadoi_command(self, command: List[str]) -> Result:
        return self.runner.invoke(mecadoi, command)

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
