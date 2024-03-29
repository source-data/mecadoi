from typing import List
import responses
from unittest import TestCase
from mecadoi.eeb.api import Article
from mecadoi.crossref.verify import verify


class TestVerifyDepositionFile(TestCase):
    @responses.activate
    def test_verify_valid_deposition_file(self) -> None:
        self.set_up_eeb_api_response()

        actual_result = verify(self.deposition_file)

        self.assertEqual(1, len(actual_result))
        verification_result = actual_result[0]
        self.assertEqual(self.preprint_doi, verification_result.preprint_doi)

        self.assertIsNone(verification_result.error)
        self.assertTrue(verification_result.all_reviews_present)

    @responses.activate
    def test_verify_invalid_deposition_file(self) -> None:
        self.eeb_api_response[0]["review_process"]["reviews"] = []
        self.set_up_eeb_api_response()

        actual_result = verify(self.deposition_file)

        self.assertEqual(1, len(actual_result))
        verification_result = actual_result[0]
        self.assertEqual(self.preprint_doi, verification_result.preprint_doi)

        self.assertIsNotNone(verification_result.error)
        self.assertFalse(verification_result.all_reviews_present)

    @responses.activate
    def test_verify_deposition_file_with_dois_already_assigned(self) -> None:
        fixtures = [
            # review DOIs, author reply DOI, expected result for no_dois_assigned
            ([None, None, None, None], None, True),  # no DOIs
            (["", None, None, None], None, True),  # empty DOI for a review
            ([None, None, None, None], "", True),  # empty DOI for the response
            (["doi", None, None, None], None, False),  # one review has a DOI
            ([None, None, None, None], "doi", False),  # the author reply has a DOI
            (["doi", "doi", "doi", "doi"], "doi", False),  # everything has a DOI
        ]

        for review_dois, response_doi, expected in fixtures:
            with self.subTest(
                review_dois=review_dois, response_doi=response_doi, expected=expected
            ):
                review_process = self.eeb_api_response[0]["review_process"]
                for i, review in enumerate(review_process["reviews"]):
                    doi = review_dois[i]  # type: ignore[index] # review_dois is a list
                    if doi is not None:
                        review["doi"] = doi
                response = review_process["response"]
                if response and response_doi is not None:
                    response["doi"] = response_doi

                self.set_up_eeb_api_response()

                actual_result = verify(self.deposition_file)

                self.assertEqual(1, len(actual_result))
                verification_result = actual_result[0]
                if expected:
                    self.assertIsNone(verification_result.error)
                else:
                    self.assertIsNotNone(verification_result.error)
                self.assertEqual(expected, verification_result.no_dois_assigned)

    def set_up_eeb_api_response(self) -> None:
        # Set up responses, which mocks out the requests library we use
        responses.upsert(
            responses.GET,
            f"https://eeb.embo.org/api/v1/doi/{self.preprint_doi}",
            json=self.eeb_api_response,
            status=200,
        )

    def setUp(self) -> None:
        with open("tests/resources/expected/multiple-revision-rounds.xml", "r") as f:
            self.deposition_file = f.read()
        self.preprint_doi = "10.1101/multiple-revision-rounds.123.456.7890"
        self.eeb_api_response: List[Article] = [
            {
                "id": 20585310,
                "doi": "10.1101/multiple-revision-rounds.123.456.7890",
                "version": "1.2",
                "source": "660d7c89-6c99-1014-8a48-df2e55f654d0.meca",
                "journal": "bioRxiv",
                "title": "scDVF: Single-cell Transcriptomic Deep Velocity Field Learning with Neural Ordinary [..]",
                "abstract": "Recent advances in single-cell RNA sequencing technology provided unprecedented [..]",
                "authors": [
                    {
                        "corresp": None,
                        "orcid": "http://orcid.org/0000-0002-5835-3840",
                        "position_idx": 0,
                        "given_names": "Zhanlin",
                        "surname": "Chen",
                    },
                    {
                        "corresp": None,
                        "orcid": None,
                        "position_idx": 1,
                        "given_names": "William C.",
                        "surname": "King",
                    },
                    {
                        "corresp": "yes",
                        "orcid": None,
                        "position_idx": 2,
                        "given_names": "Mark",
                        "surname": "Gerstein",
                    },
                    {
                        "corresp": "yes",
                        "orcid": None,
                        "position_idx": 3,
                        "given_names": "Jing",
                        "surname": "Zhang",
                    },
                ],
                "pub_date": "2022-02-23T00:00:00Z",
                "journal_doi": None,
                "published_journal_title": None,
                "nb_figures": 5,
                "revdate": None,
                "review_process": {
                    "reviews": [
                        {
                            "source": "cross_ref",
                            "posting_date": "2022-04-14",
                            "review_idx": "1",
                            "highlight": "Review 1: Global projections of potential lives saved from COVID-19 [..]",
                            "related_article_doi": "10.1101/multiple-revision-rounds.123.456.7890",
                            "text": "This study has been evaluated by _MIT Press - Journals_.\n\n__Review 1: [..]",
                            "reviewed_by": "MIT Press - Journals",
                            "position_idx": 0,
                        },
                        {
                            "source": "cross_ref",
                            "posting_date": "2022-04-15",
                            "review_idx": "2",
                            "highlight": "Review 2: Global projections of potential lives saved from COVID-19 [..]",
                            "related_article_doi": "10.1101/multiple-revision-rounds.123.456.7890",
                            "text": "This study has been evaluated by _MIT Press - Journals_.\n\n__Review 1: [..]",
                            "reviewed_by": "MIT Press - Journals",
                            "position_idx": 1,
                        },
                        {
                            "source": "cross_ref",
                            "posting_date": "2022-04-16",
                            "review_idx": "3",
                            "highlight": "Review 3: Global projections of potential lives saved from COVID-19 [..]",
                            "related_article_doi": "10.1101/multiple-revision-rounds.123.456.7890",
                            "text": "This study has been evaluated by _MIT Press - Journals_.\n\n__Review 1: [..]",
                            "reviewed_by": "MIT Press - Journals",
                            "position_idx": 2,
                        },
                        {
                            "source": "cross_ref",
                            "posting_date": "2022-04-17",
                            "review_idx": "4",
                            "highlight": "Review 4: Global projections of potential lives saved from COVID-19 [..]",
                            "related_article_doi": "10.1101/multiple-revision-rounds.123.456.7890",
                            "text": "This study has been evaluated by _MIT Press - Journals_.\n\n__Review 1: [..]",
                            "reviewed_by": "MIT Press - Journals",
                            "position_idx": 3,
                        },
                    ],
                    "response": {
                        "source": "cross_ref",
                        "posting_date": "2022-04-27",
                        "review_idx": "1",
                        "highlight": "Author Reply: Global projections of potential lives saved from COVID-19 [..]",
                        "related_article_doi": "10.1101/multiple-revision-rounds.123.456.7890",
                        "text": "Detailed comments to reviews:\n\n__Review 1: [..]",
                        "reviewed_by": "MIT Press - Journals",
                        "position_idx": 3,
                    },
                    "annot": [],
                },
                "entities": [],
                "assays": [
                    "gene expression",
                    "scrna-seq",
                    "gene",
                    "expression",
                ],
                "main_topics": [],
                "highlighted_entities": [],
            },
        ]

        return super().setUp()
