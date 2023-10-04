from mecadoi.meca import (
    parse_meca_archive,
    Manuscript,
    AuthorReply,
    Review,
    RevisionRound,
)
from mecadoi.model import Author, Institution, Orcid
from tests.common import MecaArchiveTestCase


class ParseMecaArchiveTestCase(MecaArchiveTestCase):
    """Verify that parsing MECA archives works as expected."""

    def test_parsing_invalid_archives(self) -> None:
        """When parsing invalid MECA archives a ValueError should be raised."""
        invalid_meca_archives = [
            self.get_meca_archive_path(meca_archive_name)
            for meca_archive_name in ["no-manifest", "no-article"]
        ]
        invalid_zip_files = ["tests/resources/expected/multiple-revision-rounds.xml"]
        for file in invalid_meca_archives + invalid_zip_files:
            with self.subTest(file=file):
                with self.assertRaises(ValueError):
                    parse_meca_archive(file)

    def test_parsing_valid_archives(self) -> None:
        """When parsing valid MECA archives an Article object with all the right info should be returned."""
        for meca_archive_name, expected_result in MANUSCRIPTS.items():
            with self.subTest(meca_archive=meca_archive_name):
                meca_archive_path = self.get_meca_archive_path(meca_archive_name)
                actual_result = parse_meca_archive(meca_archive_path)
                self.assertArticlesEqual(expected_result, actual_result)

    def assertArticlesEqual(
        self, expected_article: Manuscript, actual_article: Manuscript
    ) -> None:
        self.assertEqual(expected_article, actual_article)


INVALID_MECA_ARCHIVES = [
    "no-manifest",
    "no-article",
]


MANUSCRIPTS = {
    "no-institution": Manuscript(
        authors=[
            Author(
                given_name="Jane",
                surname="Doe",
                orcid=Orcid(
                    id="https://orcid.org/0000-0012-3456-7890", is_authenticated=True
                ),
                is_corresponding_author=True,
                institutions=[
                    Institution(
                        name="/",
                        department=None,
                        city="/",
                        country="/",
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
                        name="/",
                        department=None,
                        city="/",
                        country=None,
                    )
                ],
            ),
        ],
        text={
            "abstract": "This article has a single revision round and thus in ...",
        },
        doi="10.12345/single-revision-round.1234567890",
        preprint_doi="10.1101/single-revision-round.123.456.7890",
        journal="Review Commons - TEST",
        review_process=[
            RevisionRound(
                revision_id="0",
                reviews=[
                    Review(
                        authors=[
                            Author(
                                given_name="",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Lorem ipsum dolor sit amet.",
                        },
                        running_number="1",
                    ),
                    Review(
                        authors=[
                            Author(
                                given_name="redacted",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Between 3 and 6 months",
                            "Evidence, reproducibility and clarity (Required)": "Summary: this is a test",
                            "Significance (Required)": "Signification: also a test",
                        },
                        running_number="2",
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
                                    name="/",
                                    department=None,
                                    city="/",
                                    country="/",
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
                                    name="/",
                                    department=None,
                                    city="/",
                                    country=None,
                                )
                            ],
                        ),
                    ],
                    text={},
                ),
            ),
        ],
        title="An article with a single revision round.",
    ),
    "no-reviews": Manuscript(
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
        text={
            "abstract": "This article has no reviews and thus in ...",
        },
        doi="10.12345/no-reviews.1234567890",
        preprint_doi="10.1101/no-reviews.123.456.7890",
        journal="Review Commons - TEST",
        review_process=None,
        title="An article without reviews.",
    ),
    "no-preprint-doi": Manuscript(
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
        text={
            "abstract": "This article has no preprint DOI and thus in ...",
        },
        doi="10.12345/no-preprint-doi.1234567890",
        preprint_doi=None,
        journal="Review Commons - TEST",
        review_process=[
            RevisionRound(
                revision_id="0",
                reviews=[
                    Review(
                        authors=[
                            Author(
                                given_name="",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Lorem ipsum dolor sit amet.",
                        },
                        running_number="1",
                    ),
                    Review(
                        authors=[
                            Author(
                                given_name="redacted",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Between 3 and 6 months",
                            "Evidence, reproducibility and clarity (Required)": "Summary: this is a test",
                            "Significance (Required)": "Signification: also a test",
                        },
                        running_number="2",
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
                ),
            )
        ],
        title="An article without preprint DOI.",
    ),
    "no-author-reply": Manuscript(
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
        text={
            "abstract": "This article has no author reply and thus in ...",
        },
        doi="10.12345/no-author-reply.1234567890",
        preprint_doi="10.1101/no-author-reply.123.456.7890",
        journal="Review Commons - TEST",
        review_process=[
            RevisionRound(
                revision_id="0",
                reviews=[
                    Review(
                        authors=[
                            Author(
                                given_name="redacted",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Consectetur adipiscing elit.",
                        },
                        running_number="1",
                    ),
                    Review(
                        authors=[
                            Author(
                                given_name="redacted",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Sed do eiusmod tempor incididunt ut labore et dolore.",
                        },
                        running_number="2",
                    ),
                    Review(
                        authors=[
                            Author(
                                given_name="",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Cras adipiscing enim eu turpis egestas pretium aenean.",
                        },
                        running_number="3",
                    ),
                ],
                author_reply=None,
            ),
            RevisionRound(
                revision_id="1",
                reviews=[
                    Review(
                        authors=[
                            Author(
                                given_name="redacted",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Evidence, reproducibility and clarity (Required)": "This is sample of evidence answer",
                            "Significance (Required)": "This is a sample of significance",
                        },
                        running_number="1",
                    )
                ],
                author_reply=None,
            ),
        ],
        title="An article without author reply.",
    ),
    "multiple-revision-rounds": Manuscript(
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
        text={
            "abstract": "This article has multiple revision rounds and thus in ...",
        },
        doi="10.12345/multiple-revision-rounds.1234567890",
        preprint_doi="10.1101/multiple-revision-rounds.123.456.7890",
        journal="Review Commons - TEST",
        review_process=[
            RevisionRound(
                revision_id="0",
                reviews=[
                    Review(
                        authors=[
                            Author(
                                given_name="redacted",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Lorem ipsum dolor sit amet.",
                        },
                        running_number="1",
                    ),
                    Review(
                        authors=[
                            Author(
                                given_name="redacted",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Consectetur adipiscing elit.",
                        },
                        running_number="2",
                    ),
                    Review(
                        authors=[
                            Author(
                                given_name="",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Sed do eiusmod tempor incididunt ut labore.",
                        },
                        running_number="3",
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
                ),
            ),
            RevisionRound(
                revision_id="1",
                reviews=[
                    Review(
                        authors=[
                            Author(
                                given_name="redacted",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            )
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Evidence, reproducibility and clarity (Required)": "This is sample of evidence answer",
                            "Significance (Required)": "This is a sample of significance",
                        },
                        running_number="1",
                    )
                ],
                author_reply=None,
            ),
        ],
        title="An article with multiple revision rounds.",
    ),
    "single-revision-round": Manuscript(
        authors=[
            Author(
                given_name="Jane",
                surname="Doe",
                orcid=Orcid(
                    id="https://orcid.org/0000-0012-3456-7890", is_authenticated=True
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
        text={
            "abstract": "This article has a single revision round and thus in ...",
        },
        doi="10.12345/single-revision-round.1234567890",
        preprint_doi="10.1101/single-revision-round.123.456.7890",
        journal="Review Commons - TEST",
        review_process=[
            RevisionRound(
                revision_id="0",
                reviews=[
                    Review(
                        authors=[
                            Author(
                                given_name="",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Cannot tell / Not applicable",
                            "Significance (Required)": "Lorem ipsum dolor sit amet.",
                        },
                        running_number="1",
                    ),
                    Review(
                        authors=[
                            Author(
                                given_name="redacted",
                                surname="redacted",
                                orcid=None,
                                is_corresponding_author=False,
                                institutions=[],
                            ),
                        ],
                        text={
                            "Estimated time to Complete Revisions (Required)": "Between 3 and 6 months",
                            "Evidence, reproducibility and clarity (Required)": "Summary: this is a test",
                            "Significance (Required)": "Signification: also a test",
                        },
                        running_number="2",
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
                ),
            ),
        ],
        title="An article with a single revision round.",
    ),
}
