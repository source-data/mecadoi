from datetime import datetime
from os import remove
from re import escape
from sqlite3 import IntegrityError
from unittest import TestCase
from unittest.mock import MagicMock, patch
from src.config import DOI_DB_FILE, DOI_TEMPLATE
from src.dois import DoiDatabase, get_free_doi


class DoiTestCase(TestCase):

    def setUp(self) -> None:
        try:
            remove(DOI_DB_FILE)
        except FileNotFoundError:
            pass
        DoiDatabase(DOI_DB_FILE).initialize()
        return super().setUp()

    def test_creates_good_dois(self) -> None:
        pattern_expected_doi = (
            escape(DOI_TEMPLATE)  # escapes . and $ signs
            .replace('\\$year', str(datetime.now().year))  # $year should be substituted with the current year
            .replace('\\$random', '[0-9]{6}')  # $random should be substituted with 6 random digits
        )
        num_dois_to_test = 100
        actual_dois = [get_free_doi(str(i)) for i in range(num_dois_to_test)]
        self.assertEqual(num_dois_to_test, len(actual_dois))

        for actual_doi in actual_dois:
            with self.subTest(doi=actual_doi):
                self.assertRegex(actual_doi, pattern_expected_doi)

    @patch('src.dois.DoiDatabase')
    def test_fails_to_create_doi_if_present_in_db(self, mocked_doi_db: MagicMock) -> None:
        mocked_doi_db.return_value.mark_doi_as_used.side_effect = IntegrityError('')
        self.assertRaises(Exception, get_free_doi, 'test')
