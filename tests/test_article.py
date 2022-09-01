from datetime import datetime
from unittest import TestCase
from src.article import (
    from_meca_manuscript,
    Article,
    AuthorReply,
    Review,
    RevisionRound,
)
from src.model import Author, Institution, Orcid
from tests.test_meca import MANUSCRIPTS

DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES = "10.15252/rc.2020123456"
PUBLICATION_DATE = datetime(2020, 10, 20)


class ArticleTestCase(TestCase):
    """Verify that parsing MECA manuscripts works as expected."""

    def setUp(self) -> None:
        self.doi_generator = lambda s: DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES
        return super().setUp()

    def test_parsing_invalid_manuscripts(self) -> None:
        """When parsing invalid manuscripts a ValueError should be raised."""
        for manuscript_name in INVALID_MANUSCRIPTS:
            with self.subTest(manuscript=manuscript_name):
                manuscript = MANUSCRIPTS[manuscript_name]
                with self.assertRaises(ValueError):
                    from_meca_manuscript(
                        manuscript, PUBLICATION_DATE, self.doi_generator
                    )

    def test_parsing_valid_manuscripts(self) -> None:
        """When parsing valid manuscripts an Article object with all the right info should be returned."""
        for manuscript_name, expected_result in ARTICLES.items():
            with self.subTest(manuscript=manuscript_name):
                manuscript = MANUSCRIPTS[manuscript_name]
                actual_result = from_meca_manuscript(
                    manuscript, PUBLICATION_DATE, self.doi_generator
                )
                self.assertArticlesEqual(expected_result, actual_result)

    def test_parsing_manuscript_with_passed_in_doi(self) -> None:
        """Parsing a manuscript without preprint DOI should work when passing in a preprint DOI"""
        manuscript = MANUSCRIPTS["no-preprint-doi"]
        self.assertIsNone(manuscript.preprint_doi)

        passed_in_preprint_doi = "10.1234/preprint-doi.567890"
        actual_result = from_meca_manuscript(
            manuscript,
            PUBLICATION_DATE,
            self.doi_generator,
            preprint_doi=passed_in_preprint_doi,
        )

        expected_result = Article(
            doi=passed_in_preprint_doi,
            title="An article without preprint DOI.",
            review_process=[
                RevisionRound(
                    reviews=[
                        Review(
                            authors=[],
                            text={
                                "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                                "Significance (Required)": "Lorem ipsum dolor sit amet.",
                            },
                            doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                            publication_date=PUBLICATION_DATE,
                        ),
                        Review(
                            authors=[],
                            text={
                                "Estimated time to Complete Revisions (Required)": "Between 3 and 6 months",
                                "Evidence, reproducibility and clarity (Required)": "Summary: this is a test",
                                "Significance (Required)": "Signification: also a test",
                            },
                            doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                            publication_date=PUBLICATION_DATE,
                        ),
                    ],
                    author_reply=AuthorReply(
                        authors=[
                            Author(
                                given_name="Jane",
                                surname="Doe",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[
                                    Institution(
                                        name="EMBL",
                                        department="Medicinal Chemistry",
                                        city="Heidelberg",
                                        country="Germany",
                                    )
                                ],
                            ),
                            Author(
                                given_name="John",
                                surname="Doe",
                                orcid=None,
                                is_corresponding_author=True,
                                institutions=[
                                    Institution(
                                        name="EMBL",
                                        department="Medicinal Chemistry",
                                        city="Heidelberg",
                                        country="Germany",
                                    )
                                ],
                            ),
                        ],
                        text={},
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                ),
            ],
        )

        self.assertArticlesEqual(expected_result, actual_result)

    def assertArticlesEqual(
        self, expected_article: Article, actual_article: Article
    ) -> None:
        self.assertEqual(expected_article, actual_article)


INVALID_MANUSCRIPTS = [
    "no-reviews",
    "no-preprint-doi",
]

ARTICLES = {
    "no-author-reply": Article(
        doi="10.1101/no-author-reply.123.456.7890",
        title="An article without author reply.",
        review_process=[
            RevisionRound(
                reviews=[
                    Review(
                        authors=[],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Consectetur adipiscing elit.",
                        },
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                    Review(
                        authors=[],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Sed do eiusmod tempor incididunt ut labore et dolore.",
                        },
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                    Review(
                        authors=[],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Cras adipiscing enim eu turpis egestas pretium aenean.",
                        },
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                ],
                author_reply=None,
            ),
            RevisionRound(
                reviews=[
                    Review(
                        authors=[],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Evidence, reproducibility and clarity (Required)": "This is sample of evidence answer",
                            "Significance (Required)": "This is a sample of significance",
                        },
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                ],
                author_reply=None,
            ),
        ],
    ),
    "multiple-revision-rounds": Article(
        doi="10.1101/multiple-revision-rounds.123.456.7890",
        title="An article with multiple revision rounds.",
        review_process=[
            RevisionRound(
                reviews=[
                    Review(
                        authors=[],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Lorem ipsum dolor sit amet.",
                        },
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                    Review(
                        authors=[],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Consectetur adipiscing elit.",
                        },
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                    Review(
                        authors=[],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Sed do eiusmod tempor incididunt ut labore.",
                        },
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                ],
                author_reply=AuthorReply(
                    authors=[
                        Author(
                            given_name="Jane",
                            surname="Doe",
                            orcid=None,
                            is_corresponding_author=True,
                            institutions=[
                                Institution(
                                    name="EMBL",
                                    department="Medicinal Chemistry",
                                    city="Heidelberg",
                                    country="Germany",
                                )
                            ],
                        ),
                        Author(
                            given_name="John",
                            surname="Doe",
                            orcid=None,
                            is_corresponding_author=False,
                            institutions=[
                                Institution(
                                    name="EMBL",
                                    department="Medicinal Chemistry",
                                    city="Heidelberg",
                                    country="Germany",
                                )
                            ],
                        ),
                    ],
                    text={},
                    doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                    publication_date=PUBLICATION_DATE,
                ),
            ),
            RevisionRound(
                reviews=[
                    Review(
                        authors=[],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Evidence, reproducibility and clarity (Required)": "This is sample of evidence answer",
                            "Significance (Required)": "This is a sample of significance",
                        },
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                ],
                author_reply=None,
            ),
        ],
    ),
    "single-revision-round": Article(
        doi="10.1101/single-revision-round.123.456.7890",
        title="An article with a single revision round.",
        review_process=[
            RevisionRound(
                reviews=[
                    Review(
                        authors=[],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Lorem ipsum dolor sit amet.",
                        },
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                    Review(
                        authors=[],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Between 3 and 6 months",
                            "Evidence, reproducibility and clarity (Required)": "Summary: this is a test",
                            "Significance (Required)": "Signification: also a test",
                        },
                        doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                        publication_date=PUBLICATION_DATE,
                    ),
                ],
                author_reply=AuthorReply(
                    authors=[
                        Author(
                            given_name="Jane",
                            surname="Doe",
                            orcid=Orcid(
                                id="https://orcid.org/0000-0012-3456-7890",
                                is_authenticated=True,
                            ),
                            is_corresponding_author=True,
                            institutions=[
                                Institution(
                                    name="EMBL",
                                    department="Medicinal Chemistry",
                                    city="Heidelberg",
                                    country="Germany",
                                )
                            ],
                        ),
                        Author(
                            given_name="John",
                            surname="Doe",
                            orcid=None,
                            is_corresponding_author=False,
                            institutions=[
                                Institution(
                                    name="EMBL",
                                    department="Medicinal Chemistry",
                                    city="Heidelberg",
                                    country="Germany",
                                )
                            ],
                        ),
                    ],
                    text={},
                    doi=DOI_FOR_REVIEWS_AND_AUTHOR_REPLIES,
                    publication_date=PUBLICATION_DATE,
                ),
            ),
        ],
    ),
}
