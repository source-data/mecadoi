from typing import List
from unittest import TestCase
from click.testing import CliRunner, Result
from src.cli.main import main as mecadoi


class CliTestCase(TestCase):

    def setUp(self) -> None:
        self.runner = CliRunner()
        return super().setUp()

    def run_mecadoi_command(self, command: List[str]) -> Result:
        return self.runner.invoke(mecadoi, command)

    def test_meca_info(self) -> None:
        test_file = 'src/test/test_data/mutagenesis.zip'
        title = 'Mutagenesis of the ADAM17-phosphatidylserine-binding motif leads to embryonic lethality in mice'
        doi = '10.26508/lsa.201900430'
        preprint_doi = '10.1101/2022.02.15.480564'
        publisher = 'Review Commons - TEST'
        year = '2020'
        result = self.run_mecadoi_command(['meca', 'info', test_file])
        self.assertEqual(0, result.exit_code)
        self.assertIn(title, result.output)
        self.assertIn(doi, result.output)
        self.assertIn(preprint_doi, result.output)
        self.assertIn(publisher, result.output)
        self.assertIn(year, result.output)
