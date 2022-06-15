"""
Data classes that act as interfaces between the modules of this project.

The main entrypoint is the `Article` class.
"""

__all__ = [
    'Author',
    'DigitalObject',
    'Orcid',
    'Work',
]

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DigitalObject:
    """
    Something that has a Digital Object Identifier (DOI).

    Could be a journal article, a book, etc.
    """

    doi: str
    """
    The Digital Object Identifier (DOI) of this digital object.

    Is of the form `prefix/suffix` where `prefix` is usually something like "10.1111" and identifies the registrant of
    this DOI, and suffix is chosen by the registrant and usually a random string of numbers and letters.
    """


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
    """
    The author(s) of this piece of scholarly work.

    If no authors are given the work was produced by anonymous author(s).
    """

    text: Dict[str, str]
    """
    The text of this scholarly work.

    It's represented as a dict where the keys are the title of its section and the values the actual text. An article
    would have an "abstract" section, a referee report a "Significance" section, etc.
    """
