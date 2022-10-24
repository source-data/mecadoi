"""

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
    """"""
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
