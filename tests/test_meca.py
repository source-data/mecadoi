from src.meca import parse_meca_archive
from src.model import Article, Author, AuthorReply, Orcid, Review, RevisionRound
from tests.common import MecaArchiveTestCase


class ParseMecaArchiveTestCase(MecaArchiveTestCase):
    """Verify that parsing MECA archives works as expected."""

    def test_parsing_invalid_archives(self) -> None:
        """When parsing invalid MECA archives a ValueError should be raised."""
        for meca_archive in self.INVALID_MECA_ARCHIVES:
            with self.subTest(meca_archive=meca_archive):
                with self.assertRaises(ValueError):
                    parse_meca_archive(meca_archive)

    def test_parsing_valid_archives(self) -> None:
        """When parsing valid MECA archives an Article object with all the right info should be returned."""
        for meca_archive, expected_result in self.EXPECTED_RESULTS.items():
            with self.subTest(meca_archive=meca_archive):
                actual_result = parse_meca_archive(meca_archive)
                self.assertArticlesEqual(expected_result, actual_result)

    def assertArticlesEqual(self, expected_article: Article, actual_article: Article) -> None:
        self.assertEqual(expected_article, actual_article)

    INVALID_MECA_ARCHIVES = [
        f'{MecaArchiveTestCase.MECA_TARGET_DIR}/no-manifest.zip',
        f'{MecaArchiveTestCase.MECA_TARGET_DIR}/no-article.zip',
    ]

    EXPECTED_RESULTS = {
        f'{MecaArchiveTestCase.MECA_TARGET_DIR}/no-reviews.zip': Article(
            authors=[
                Author(given_name='Jane', surname='Doe', orcid=None, affiliation='EMBL', is_corresponding_author=True),
                Author(given_name='John', surname='Doe', orcid=None, affiliation='EMBL', is_corresponding_author=False),
            ],
            text={
                'abstract': 'This article has no reviews and thus in ...',
            },
            doi='10.12345/no-reviews.1234567890',
            preprint_doi='10.1101/no-reviews.123.456.7890',
            journal='Review Commons - TEST',
            review_process=None,
            title='An article without reviews.',
        ),
        f'{MecaArchiveTestCase.MECA_TARGET_DIR}/no-preprint-doi.zip': Article(
            authors=[
                Author(given_name='Jane', surname='Doe', orcid=None, affiliation='EMBL', is_corresponding_author=False),
                Author(given_name='John', surname='Doe', orcid=None, affiliation='EMBL', is_corresponding_author=True),
            ],
            text={
                'abstract': 'This article has no preprint DOI and thus in ...',
            },
            doi='10.12345/no-preprint-doi.1234567890',
            preprint_doi=None,
            journal='Review Commons - TEST',
            review_process=[
                RevisionRound(
                    revision_id='0',
                    reviews=[
                        Review(
                            authors=[
                                Author(given_name='', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Significance (Required)': 'Lorem ipsum dolor sit amet.',
                                'Estimated time to Complete Revisions (Required)': 'Cannot tell / Not applicable',
                            },
                            running_number='1',
                        ),
                        Review(
                            authors=[
                                Author(given_name='redacted', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Evidence, reproducibility and clarity (Required)': 'Summary: this is a test',
                                'Significance (Required)': 'Signification: also a test',
                                'Estimated time to Complete Revisions (Required)': 'Between 3 and 6 months',
                            },
                            running_number='2'
                        )
                    ],
                    author_reply=AuthorReply(
                        authors=[
                            Author(given_name='Jane', surname='Doe', orcid=None, affiliation='EMBL',
                                   is_corresponding_author=False),
                            Author(given_name='John', surname='Doe', orcid=None, affiliation='EMBL',
                                   is_corresponding_author=True),
                        ],
                        text={},
                    )
                )
            ],
            title='An article without preprint DOI.',
        ),
        f'{MecaArchiveTestCase.MECA_TARGET_DIR}/no-author-reply.zip': Article(
            authors=[
                Author(given_name='Jane', surname='Doe', orcid=None, affiliation='EMBL', is_corresponding_author=True),
                Author(given_name='John', surname='Doe', orcid=None, affiliation='EMBL', is_corresponding_author=False),
            ],
            text={
                'abstract': 'This article has no author reply and thus in ...',
            },
            doi='10.12345/no-author-reply.1234567890',
            preprint_doi='10.1101/no-author-reply.123.456.7890',
            journal='Review Commons - TEST',
            review_process=[
                RevisionRound(
                    revision_id='0',
                    reviews=[
                        Review(
                            authors=[
                                Author(given_name='redacted', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Significance (Required)': 'Consectetur adipiscing elit.',
                                'Estimated time to Complete Revisions (Required)': 'Cannot tell / Not applicable'
                            },
                            running_number='1',
                        ),
                        Review(
                            authors=[
                                Author(given_name='redacted', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Significance (Required)': 'Sed do eiusmod tempor incididunt ut labore et dolore.',
                                'Estimated time to Complete Revisions (Required)': 'Cannot tell / Not applicable'
                            },
                            running_number='2'
                        ),
                        Review(
                            authors=[
                                Author(given_name='', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Significance (Required)': 'Cras adipiscing enim eu turpis egestas pretium aenean.',
                                'Estimated time to Complete Revisions (Required)': 'Cannot tell / Not applicable',
                            },
                            running_number='3',
                        )
                    ],
                    author_reply=None,
                ),
                RevisionRound(
                    revision_id='1',
                    reviews=[
                        Review(
                            authors=[
                                Author(given_name='redacted', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Evidence, reproducibility and clarity (Required)': 'This is sample of evidence answer',
                                'Significance (Required)': 'This is a sample of significance',
                                'Estimated time to Complete Revisions (Required)': 'Cannot tell / Not applicable',
                            },
                            running_number='1'
                        )
                    ],
                    author_reply=None,
                )
            ],
            title='An article without author reply.',
        ),
        f'{MecaArchiveTestCase.MECA_TARGET_DIR}/multiple-revision-rounds.zip': Article(
            authors=[
                Author(given_name='Jane', surname='Doe', orcid=None, affiliation='EMBL', is_corresponding_author=True),
                Author(given_name='John', surname='Doe', orcid=None, affiliation='EMBL', is_corresponding_author=False),
            ],
            text={
                'abstract': 'This article has multiple revision rounds and thus in ...',
            },
            doi='10.12345/multiple-revision-rounds.1234567890',
            preprint_doi='10.1101/multiple-revision-rounds.123.456.7890',
            journal='Review Commons - TEST',
            review_process=[
                RevisionRound(
                    revision_id='0',
                    reviews=[
                        Review(
                            authors=[
                                Author(given_name='redacted', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Significance (Required)': 'Lorem ipsum dolor sit amet.',
                                'Estimated time to Complete Revisions (Required)': 'Cannot tell / Not applicable',
                            },
                            running_number='1'
                        ),
                        Review(
                            authors=[
                                Author(given_name='redacted', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Significance (Required)': 'Consectetur adipiscing elit.',
                                'Estimated time to Complete Revisions (Required)': 'Cannot tell / Not applicable',
                            },
                            running_number='2'
                        ),
                        Review(
                            authors=[
                                Author(given_name='', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Significance (Required)': 'Sed do eiusmod tempor incididunt ut labore.',
                                'Estimated time to Complete Revisions (Required)': 'Cannot tell / Not applicable',
                            },
                            running_number='3',
                        ),
                    ],
                    author_reply=AuthorReply(
                        authors=[
                            Author(given_name='Jane', surname='Doe', orcid=None, affiliation='EMBL',
                                   is_corresponding_author=True),
                            Author(given_name='John', surname='Doe', orcid=None, affiliation='EMBL',
                                   is_corresponding_author=False),
                        ],
                        text={},
                    )
                ),
                RevisionRound(
                    revision_id='1',
                    reviews=[
                        Review(
                            authors=[
                                Author(given_name='redacted', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False)],
                            text={
                                'Evidence, reproducibility and clarity (Required)': 'This is sample of evidence answer',
                                'Significance (Required)': 'This is a sample of significance',
                                'Estimated time to Complete Revisions (Required)': 'Cannot tell / Not applicable'
                            },
                            running_number='1'
                        )
                    ],
                    author_reply=None,
                ),
            ],
            title='An article with multiple revision rounds.',
        ),
        f'{MecaArchiveTestCase.MECA_TARGET_DIR}/single-revision-round.zip': Article(
            authors=[
                Author(
                    given_name='Jane',
                    surname='Doe',
                    orcid=Orcid(id='https://orcid.org/0000-0012-3456-7890', is_authenticated=True),
                    affiliation='EMBL',
                    is_corresponding_author=True
                ),
                Author(given_name='John', surname='Doe', orcid=None, affiliation='EMBL', is_corresponding_author=False),
            ],
            text={
                'abstract': 'This article has a single revision round and thus in ...',
            },
            doi='10.12345/single-revision-round.1234567890',
            preprint_doi='10.1101/single-revision-round.123.456.7890',
            journal='Review Commons - TEST',
            review_process=[
                RevisionRound(
                    revision_id='0',
                    reviews=[
                        Review(
                            authors=[
                                Author(given_name='', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Significance (Required)': 'Lorem ipsum dolor sit amet.',
                                'Estimated time to Complete Revisions (Required)': 'Cannot tell / Not applicable',
                            },
                            running_number='1'
                        ),
                        Review(
                            authors=[
                                Author(given_name='redacted', surname='redacted', orcid=None, affiliation=None,
                                       is_corresponding_author=False),
                            ],
                            text={
                                'Evidence, reproducibility and clarity (Required)': 'Summary: this is a test',
                                'Significance (Required)': 'Signification: also a test',
                                'Estimated time to Complete Revisions (Required)': 'Between 3 and 6 months',
                            },
                            running_number='2'
                        ),
                    ],
                    author_reply=AuthorReply(
                        authors=[
                            Author(
                                given_name='Jane',
                                surname='Doe',
                                orcid=Orcid(id='https://orcid.org/0000-0012-3456-7890', is_authenticated=True),
                                affiliation='EMBL',
                                is_corresponding_author=True
                            ),
                            Author(given_name='John', surname='Doe', orcid=None, affiliation='EMBL',
                                   is_corresponding_author=False),
                        ],
                        text={},
                    )
                ),
            ],
            title='An article with a single revision round.',
        ),
    }
