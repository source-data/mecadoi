from src.crossref.dois import get_free_doi
from .common import DoiDbTestCase


class TestDoiRetrieval(DoiDbTestCase):

    DOIS = [
        '10.15252/FPJI9780',
        '10.15252/RNOO6673',
        '10.15252/OKTO4970',
        '10.15252/BPFV1875',
        '10.15252/PWQB7290',
    ]

    RESOURCES = [
        'www.example.org',
        'example.org',
        'www.embo.org',
        'www.embl.org',
        'www.embl.de',
    ]

    def test_get_free_dois(self) -> None:
        """Verify that no DOI is returned twice."""
        free_dois = [doi for doi in self.DOIS]
        for resource in self.RESOURCES:
            with self.subTest(resource=resource):
                free_doi = get_free_doi(resource, self.DOI_DB_FILE, warning_threshold=None)
                self.assertIn(free_doi, free_dois)
                free_dois.remove(free_doi)

    def test_no_more_free_dois(self) -> None:
        """Verify that retrieving a DOI fails if no more free ones are available."""
        for resource in self.RESOURCES:
            get_free_doi(resource, self.DOI_DB_FILE, warning_threshold=None)
        with self.assertRaises(ValueError):
            get_free_doi('one resource too many', self.DOI_DB_FILE, warning_threshold=None)
