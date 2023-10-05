"""
Functions for verifying that a Crossref deposition file is valid.

The DOIs to be assigned to reviews and replies by the deposition file are checked against the Early Evidence Base (EEB)
API. EEB's API is checked because the DOIs will resolve to pages there.

The EEB API must return the same number of reviews and replies as the deposition file wants to create, and the reviews
and replies must not have any DOI assigned yet.
"""

__all__ = ["verify", "VerificationResult"]

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from xsdata.formats.dataclass.parsers import XmlParser
from mecadoi.crossref.xml.doi_batch import DoiBatch, PeerReview
from mecadoi.eeb.api import get_articles


@dataclass
class VerificationResult:
    """
    The result of verifying a Crossref deposition file.

    If the verification was successful, all fields are set to True.
    If the verification failed, the error field is set to a message describing the error.
    """

    preprint_doi: str
    """The preprint DOI that the deposition file wants to create reviews for."""
    all_reviews_present: Optional[bool] = None
    """Whether all reviews that the deposition file wants to create DOIs for are present in the EEB."""
    author_reply_matches: Optional[bool] = None
    """Whether the author reply that the deposition file wants to create a DOI for is present in the EEB."""
    no_dois_assigned: Optional[bool] = None
    """Whether none of the reviews or the author reply that the deposition file wants to create DOIs for already have a
    DOI assigned."""
    error: Optional[str] = None
    """An error message if the verification failed."""


def verify(deposition_file: str) -> List[VerificationResult]:
    """
    Checks that all DOIs to be created from the given deposition file resolve to an actual document.

    The deposition file may only contain peer review elements.

    Args:
        deposition_file: The deposition file to verify, as a string.

    Returns:
        A list of verification results, one for each preprint DOI that the deposition file wants to create DOIs for.
    """
    parser = XmlParser()

    doi_batch = parser.from_string(deposition_file, clazz=DoiBatch)

    reviews_by_preprint_doi: Dict[
        str, Tuple[List[PeerReview], Optional[PeerReview]]
    ] = {}
    for review in doi_batch.body.peer_review:
        reviewed_article_relationships = [
            rel
            for rel in review.program.related_item
            if rel.inter_work_relation.relationship_type == "isReviewOf"
        ]
        if len(reviewed_article_relationships) != 1:
            raise ValueError(
                f"Multiple isReviewOf relationships in deposition xml: {doi_batch}"
            )
        preprint_doi = reviewed_article_relationships[0].inter_work_relation.value
        reviews_by_preprint_doi.setdefault(preprint_doi, ([], None))
        (reviews, author_reply) = reviews_by_preprint_doi[preprint_doi]

        if review.type == "referee-report":
            reviews.append(review)
        elif review.type == "author-comment":
            if author_reply:
                raise ValueError(
                    f"Multiple author replies in deposition xml: {doi_batch}"
                )
            author_reply = review

        reviews_by_preprint_doi[preprint_doi] = (reviews, author_reply)

    return [
        _verify_reviews_match(preprint_doi, reviews, author_reply)
        for preprint_doi, (reviews, author_reply) in reviews_by_preprint_doi.items()
    ]


def _verify_reviews_match(
    preprint_doi: str,
    reviews: List[PeerReview],
    author_reply: Optional[PeerReview],
) -> VerificationResult:
    articles = get_articles(preprint_doi)
    if articles is None or len(articles) != 1:
        return VerificationResult(
            preprint_doi=preprint_doi,
            error=f"received no or multiple results from EEB for preprint DOI {preprint_doi}",
        )

    review_process = articles[0]["review_process"]
    eeb_reviews = review_process["reviews"]
    eeb_response = review_process["response"]

    num_reviews = len(reviews)
    num_eeb_reviews = len(eeb_reviews)
    all_reviews_present = num_eeb_reviews == num_reviews

    eeb_has_author_reply = eeb_response is not None
    deposition_has_author_reply = author_reply is not None
    author_reply_matches = eeb_has_author_reply == deposition_has_author_reply

    eeb_dois = [r.get("doi", None) for r in eeb_reviews]
    if eeb_response:
        eeb_dois += [eeb_response.get("doi", None)]
    no_dois_assigned = not any([bool(doi) for doi in eeb_dois])

    return VerificationResult(
        preprint_doi=preprint_doi,
        all_reviews_present=all_reviews_present,
        author_reply_matches=author_reply_matches,
        no_dois_assigned=no_dois_assigned,
        error=(
            None
            if all_reviews_present and author_reply_matches and no_dois_assigned
            else (
                f"deposition file wants to create DOIs for {num_reviews} reviews"
                + f'{" and an author reply" if deposition_has_author_reply else ""}'
                + f" but EEB has {num_eeb_reviews} reviews"
                + f'{" and an author reply" if eeb_has_author_reply else " and no author reply"}'
                + f'{"" if no_dois_assigned else " with DOIs already assigned"}'
            )
        ),
    )
