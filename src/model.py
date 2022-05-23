"""
Data classes that act as interfaces between the modules of this project.

The main entrypoint is the Article class that represents the article within a MECA archive.
"""

__all__ = [
    'Article',
    'Author',
    'AuthorReply',
    'Orcid',
    'Review',
    'RevisionRound',
]

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Orcid:
    """The ORCID of an author of a scholarly work that uniquely identifies them."""

    id: str
    """The actual ID. Is usually a URL to an ORCID page."""

    is_authenticated: bool
    """Wether ORCID, the service, has verified that this ORCID belongs to the author."""


@dataclass
class Author:
    """
    An author of a scholarly work.

    They have a name, an indicator wether they're the corresponding author, and optionally an affiliation and ORCID.
    """

    given_name: str
    """The given or first name of this author."""

    surname: str
    """The sur- or last name of this author."""

    orcid: Optional[Orcid]
    """The ORCID of this author to uniquely identify them."""

    affiliation: Optional[str]
    """The name of the institution that this author is mainly affiliated with."""

    is_corresponding_author: bool
    """Wether this author is the corresponding author of this scholarly work."""


@dataclass
class Work:
    """Represents a scholarly work such as an article, a referee report, or an author reply."""

    authors: List[Author]
    """The authors of this piece of scholarly work."""

    text: Dict[str, str]
    """
    The text of this scholarly work.

    It's represented as a dict where the keys are the title of its section and the values the actual text. An article
    would have an "abstract" section, a referee report a "Significance" section, etc.
    """


@dataclass
class Review(Work):
    """A referee report that reviews an article."""

    running_number: str
    """
    The running number of the referee reports in a revision round signifies their order within that round.

    As these reports are usually anonymous, the running number (or index) for example is important for the authors to
    identify which report they're replying to.
    """


@dataclass
class AuthorReply(Work):
    """The reply by the article authors to its reviews."""
    pass


@dataclass
class RevisionRound:
    """
    A round of revisions as they happen in the Review Commons workflow.

    They consist of multiple referee reports (the reviews) and, optionally, a single reply to them by the authors of
    the article.
    """

    revision_id: str
    """
    The ID of this revision round. This is taken from the MECA archive and is *probably* unique, but not guaranteed to
    be.
    """

    reviews: List[Review]
    """The referee reports written by the referees."""

    author_reply: Optional[AuthorReply]
    """The reply by the article authors to its reviews."""


@dataclass
class Article(Work):
    """
    Represents the article packaged in the MECA archive.
    """

    doi: str
    """The DOI of this article."""

    preprint_doi: Optional[str]
    """
    The DOI of the preprint that this article is based on, if such a preprint exists. It's taken from a custom-meta
    field in the article metadata.
    """

    journal: Optional[str]
    """The journal in which this article is or will be published."""

    review_process: Optional[List[RevisionRound]]
    """
    The review process this article went through, represented by a list of revision rounds. Is None if the MECA did not
    contain any information about the review process.
    """

    title: str
    """The title of this article."""
