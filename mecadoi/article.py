"""
A data model for representing articles and their review processes.

This module is intended as an intermediate representation of articles and their review processes.
Articles can be constructed from MECA manuscripts with the `from_meca_manuscript` function and can be converted into
other formats such as the Crossref deposition format.
"""

__all__ = [
    "from_meca_manuscript",
    "Article",
    "AuthorReply",
    "Review",
    "RevisionRound",
]

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional
from mecadoi.meca import Manuscript

from mecadoi.model import DigitalObject, Work


@dataclass
class Review(DigitalObject, Work):
    """A referee report that reviews an article."""

    publication_date: datetime
    """The publication date of this review."""


@dataclass
class AuthorReply(DigitalObject, Work):
    """The reply by the article authors to its reviews."""

    publication_date: datetime
    """The publication date of this review."""


@dataclass
class RevisionRound:
    """
    A round of revisions that review an article.

    Each round consists of multiple reviews and an optional reply by the authors.
    """

    reviews: List[Review]
    """The reviews written by the referees."""

    author_reply: Optional[AuthorReply]
    """The reply by the authors to the reviews in this revision round."""


@dataclass
class Article(DigitalObject):
    """An article with a list of revision rounds that each consist of peer reviews and, optionally, an author reply."""

    title: str
    """The title of this article."""

    review_process: List[RevisionRound]
    """The review process this article went through, represented by a list of revision rounds."""


def from_meca_manuscript(
    manuscript: Manuscript,
    review__process_publication_date: datetime,
    doi_generator: Callable[[str], str],
    preprint_doi: Optional[str] = None,
) -> Article:
    """
    Convert a MECA manuscript with a review process into an Article that has DOIs for all reviews and authors' replies.

    The manuscript must either have a preprint DOI or a preprint DOI must be given explicitly with the `preprint_doi`
    parameter. The preprint DOI is used as the DOI of the Article. It must also have a review process.

    The `doi_generator` function is used to generate DOIs for the reviews and the author reply. It is passed a string
    that identifies the review.

    Args:
        manuscript: The manuscript to convert.
        review__process_publication_date: The publication date of the review process.
        doi_generator: A function that generates a DOI for a given string.
        preprint_doi: The DOI of the preprint of the manuscript, if any.

    Returns:
        The converted article with DOIs for all reviews and the authors' replies.
    """
    if preprint_doi is not None:
        article_doi = preprint_doi
    elif manuscript.preprint_doi is not None:
        article_doi = manuscript.preprint_doi
    else:
        raise ValueError("no preprint DOI found in the given manuscript")

    if not manuscript.review_process:
        raise ValueError("no reviews found in the given manuscript")

    return Article(
        doi=article_doi,
        title=manuscript.title,
        review_process=[
            RevisionRound(
                reviews=[
                    Review(
                        authors=[],
                        text=review.text,
                        doi=doi_generator(
                            f"{article_doi} - {revision_round.revision_id} - {review.running_number}"
                        ),
                        publication_date=review__process_publication_date,
                    )
                    for review in revision_round.reviews
                ],
                author_reply=AuthorReply(
                    authors=revision_round.author_reply.authors,
                    text=revision_round.author_reply.text,
                    doi=doi_generator(
                        f"{article_doi} - {revision_round.revision_id} - author reply"
                    ),
                    publication_date=review__process_publication_date,
                )
                if revision_round.author_reply
                else None,
            )
            for revision_round in manuscript.review_process
        ],
    )
