from datetime import datetime
from re import escape
from sqlalchemy.exc import IntegrityError
from unittest.mock import Mock
from mecadoi.config import DOI_TEMPLATE
from mecadoi.dois import get_free_doi
from tests.test_db import BatchDbTestCase


class DoiTestCase(BatchDbTestCase):
    def test_creates_good_dois(self) -> None:
        pattern_expected_doi = (
            escape(DOI_TEMPLATE)  # escapes . and $ signs
            .replace(
                "\\$year", str(datetime.now().year)
            )  # $year should be substituted with the current year
            .replace(
                "\\$random", "[0-9]{6}"
            )  # $random should be substituted with 6 random digits
        )
        num_dois_to_test = 100
        actual_dois = [get_free_doi(self.db, str(i)) for i in range(num_dois_to_test)]
        self.assertEqual(num_dois_to_test, len(actual_dois))

        for actual_doi in actual_dois:
            with self.subTest(doi=actual_doi):
                self.assertRegex(actual_doi, pattern_expected_doi)

    def test_fails_to_create_doi_if_present_in_db(self) -> None:
        mocked_doi_db = Mock()
        attrs = {
            "mark_doi_as_used.side_effect": IntegrityError(
                "DOI already used!", None, None
            )
        }
        mocked_doi_db.configure_mock(**attrs)
        with self.assertRaises(Exception):
            get_free_doi(mocked_doi_db, "test")
