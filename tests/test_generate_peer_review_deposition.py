from datetime import datetime
from mecadoi.crossref.peer_review import generate_peer_review_deposition
from tests.common import DepositionFileTestCase, MecaArchiveTestCase
from tests.test_article import ARTICLES


class TestGeneratePeerReviewDeposition(MecaArchiveTestCase, DepositionFileTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.fixtures = [
            "multiple-revision-rounds",
            "no-author-reply",
            "no-institution",
            "single-revision-round",
        ]
        self.publication_date = datetime(2020, 10, 10)
        self.doi_for_review = "10.15252/rc.2020123456"
        self.maxDiff = None

    def test_generate_peer_review_deposition(self) -> None:
        for article_name in self.fixtures:
            with self.subTest(article=article_name):
                with open(f"tests/resources/expected/{article_name}.xml", "r") as f:
                    expected_xml = f.read()

                article = ARTICLES[article_name]
                actual_xml = generate_peer_review_deposition([article])

                self.assertDepositionFileEquals(expected_xml, actual_xml)
