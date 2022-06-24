"""
Functionality for interacting with Manuscript Exchange Common Approach (MECA) archives.

This data format was introduced as an interface between various publishing systems to allow the transferral of
manuscripts between different publishers. A single MECA archive contains a single manuscript, optionally peer
reviews of that manuscript, and can contain any further data related to the manuscript.

`parse_meca_archive()` is the main entrypoint that parses a MECA archive into a `Manuscript`, the intermediate format
defined in this module.
"""

__all__ = [
    'parse_meca_archive',
    'AuthorReply',
    'Manuscript',
    'Review',
    'RevisionRound',
]

from dataclasses import dataclass
from datetime import datetime
from html import unescape
from lxml.etree import parse, tostring
from pathlib import Path
from typing import Any, IO, List, Optional, Set, Union
from zipfile import BadZipFile, ZipFile

from src.model import Author, DigitalObject, Orcid, Work


@dataclass
class Review(Work):
    """A referee report that reviews an article, as it appears in a MECA archive."""

    running_number: str
    """
    The running number of the referee reports in a revision round signifies their order within that round.

    As these reports are usually anonymous, the running number (or index) for example is important for the authors to
    identify which report they're replying to.
    """


@dataclass
class AuthorReply(Work):
    """The reply by the article authors to its reviews, as it appears in a MECA archive."""
    pass


@dataclass
class RevisionRound:
    """
    A round of revisions as they appear in a MECA archive.

    Each round consists of multiple reviews and an optional reply by the authors.
    """

    revision_id: str
    """
    The ID of this revision round. This is taken from the MECA archive and is *probably* unique, but not guaranteed to
    be.
    """

    reviews: List[Review]
    """The reviews written by the referees."""

    author_reply: Optional[AuthorReply]
    """The reply by the authors to the reviews in this revision round."""


@dataclass
class Manuscript(DigitalObject, Work):
    """
    Represents the article packaged in a MECA archive.
    """

    title: str
    """The title of this article."""

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


def parse_meca_archive(path_to_archive: Union[str, Path], use_preprint_doi: bool = True) -> Manuscript:
    """
    Read the MECA archive at the given path and construct an Article from it.

    Raises exceptions if the MECA archive does not contain the necessary data that is required by the MECA standard
    such as a file with article metadata.
    """

    meca = MECArchive(path_to_archive)
    article_xml = meca.get_xml(MECArchive.ARTICLE)

    article_authors = _get_authors(
        article_xml.find('front/article-meta/contrib-group'),
        contrib_type='author'
    )

    try:
        review_xml = meca.get_xml(MECArchive.REVIEWS)
    except ValueError:
        review_xml = None

    if review_xml is not None:
        author_replies = meca._get_files_of_type(MECArchive.AUTHOR_REPLY)
        review_process = _get_review_process(review_xml, article_authors, author_replies)
    else:
        review_process = None

    abstract_node = article_xml.find('front/article-meta/abstract')
    return Manuscript(
        authors=article_authors,
        doi=_text(article_xml.find('front/article-meta/article-id[@pub-id-type="doi"]')),
        preprint_doi=_get_preprint_doi(article_xml),
        journal=_text_or_default(article_xml.find('front/journal-meta/journal-title-group/journal-title')),
        review_process=review_process,
        text={
            'abstract': _text(abstract_node),
        } if abstract_node is not None else {},
        title=_text(article_xml.find('front/article-meta/title-group/article-title')),
    )


def _assigned_date(review_xml: Any) -> datetime:
    date_assigned_xml = review_xml.find('history/date[@date-type="assigned"]')
    return datetime(
        _int(date_assigned_xml.find('year')),
        _int(date_assigned_xml.find('month')),
        _int(date_assigned_xml.find('day')),
    )


def _get_review_process(
    review_xml: Any,
    article_authors: List[Author],
    author_replies: List['FileInMeca']
) -> Optional[List[RevisionRound]]:
    review_process = []
    for revision_round_xml in review_xml.findall('version'):
        revision_id = revision_round_xml.get('revision')
        author_reply_present = (
            True if len(list(filter(lambda f: f.version == revision_id, author_replies))) > 0
            else False
        )

        revision_round = RevisionRound(
            revision_id=revision_id,
            reviews=[
                Review(
                    authors=_get_authors(review_xml.find('contrib-group'), contrib_type='reviewer'),
                    running_number=str(running_number),
                    text={
                        _text(review_item_xml.find('review-item-question/alt-title')): _text(review_item_xml.find(
                            'review-item-response/text'))
                        for review_item_xml in review_xml.findall('review-item-group/review-item')
                    },
                )
                for running_number, review_xml in enumerate(
                    sorted(revision_round_xml.findall('review'), key=_assigned_date),
                    start=1
                )
            ],
            author_reply=AuthorReply(
                authors=article_authors,
                text={},
            ) if author_reply_present else None,
        )
        review_process.append(revision_round)
    return review_process


def _get_preprint_doi(article_xml: Any) -> Optional[str]:
    for custom_meta in article_xml.findall('front/article-meta/custom-meta-group/custom-meta'):
        if 'Pre-existing BioRxiv Preprint DOI' == _text(custom_meta.find('meta-name')):
            return _text(custom_meta.find('meta-value'))
    return None


def _get_authors(contrib_group_xml: Any, contrib_type: str) -> List[Author]:
    authors_xml = contrib_group_xml.findall(f'contrib[@contrib-type="{contrib_type}"]')

    authors: List[Author] = []
    for author_xml in authors_xml:
        orcid_xml = author_xml.find('contrib-id[@contrib-id-type="orcid"]')
        authors.append(
            Author(
                given_name=_text(author_xml.find('name/given-names')),
                surname=_text(author_xml.find('name/surname')),
                orcid=Orcid(
                    id=_text(orcid_xml),
                    is_authenticated=orcid_xml.get('specific-use') == 'authenticated',
                ) if orcid_xml is not None else None,
                affiliation=_get_affiliation(contrib_group_xml, author_xml),
                is_corresponding_author=author_xml.get('corresp') == 'yes',
            )
        )
    return authors


def _get_affiliation(contrib_group_xml: Any, author_xml: Any) -> Optional[str]:
    aff_xref = author_xml.find('xref[@ref-type="aff"]')
    if aff_xref is not None:
        aff_id = aff_xref.get('rid')
        if aff_id is not None:
            institution = contrib_group_xml.find(f'aff[@id="{aff_id}"]/institution')
            if institution is not None:
                return _text(institution)
    return None


def _text(node: Any) -> str:
    return unescape(  # replace all entity references like &scedil; to their corresponding unicode characters
        str(
            tostring(
                node,
                method='text',  # return only text content, no <tag>s
                encoding=str,  # return an unencoded unicode string
            ).strip()  # remove trailing whitespace
        )
    )


def _text_or_default(node: Any, default: Optional[str] = None) -> Optional[str]:
    if node is None:
        return default
    return _text(node)


def _int(node: Any) -> int:
    return int(_text(node))


@dataclass(unsafe_hash=True)
class FileInMeca:
    """
    Represents a file in a MECA archive.

    Modelled after a MECA manifest's <item>s.
    """
    id: str
    file_name: str
    media_type: str
    type: str
    version: str


class MECArchive:
    """
    Encapsulates a MECA archive.

    A MECA archive is a ZIP-compressed folder of files. Within it, a file called "manifest.xml" must be present and
    contain an index of all files in the archive. Further, the archive must contain files with transfer and article
    metadata and can contain files with the peer review process and author reply.
    These can have custom names but must be listed in the manifest file with the file types specified in the class
    variables below.

    To get started, pass a zipfile.ZipFile to the constructor of this class: `meca = MECArchive(zip_file)`. This parses
    the manifest and raises a ValueError if it is not present. Then, call `meca.get_xml(MECArchive.ARTICLE)` to parse
    the XML file that contains metadata about the manuscript.

    For simplicity, the ZIP archive is opened and closed during every read of files within the archive, i.e. once at
    instantiation of this class and again during every call to get_xml().
    """

    # The file types of entries in the manifest file that are of interest to us. AUTHOR_REPLY is likely specific to
    # MECA archives exported from eJP.
    ARTICLE = 'article-metadata'
    REVIEWS = 'review-metadata'
    AUTHOR_REPLY = 'Response to Reviewers'

    def __init__(self, path_to_archive: Union[str, Path]) -> None:
        self.path_to_archive = path_to_archive

        with self._open_archive() as archive:
            self.files_in_archive = archive.namelist()

        filename_manifest = 'manifest.xml'
        if filename_manifest not in self.files_in_archive:
            raise ValueError('Invalid MECA archive: missing manifest file')

        manifest = self._parse_xml(filename_manifest)

        self.files_in_manifest: Set[FileInMeca] = set()
        for item in manifest.findall('item'):
            file_id = item.get('id')
            file_type = item.get('type')
            file_version = item.get('version')

            instance = item.find('instance')
            file_name = instance.get('href')
            media_type = instance.get('media-type')

            self.files_in_manifest.add(
                FileInMeca(
                    id=file_id,
                    file_name=file_name,
                    media_type=media_type,
                    type=file_type,
                    version=file_version,
                )
            )

    def _open_archive(self) -> ZipFile:
        try:
            return ZipFile(self.path_to_archive, 'r')
        except BadZipFile as e:
            raise ValueError('Bad zip file: ' + str(e))

    def _open_file_in_archive(self, file: Union[str, FileInMeca]) -> IO[bytes]:
        with self._open_archive() as archive:
            try:
                file_name = file.file_name  # type: ignore[union-attr] # handled by try/except block
            except AttributeError:
                file_name = file
            return archive.open(file_name)

    def _parse_xml(self, file: Union[str, FileInMeca]) -> Any:
        """Parse the given file and return an lxml.etree.Element."""
        with self._open_file_in_archive(file) as xml_file:
            tree = parse(xml_file)
            return tree.getroot()

    def _get_files_of_type(self, file_type: str, version: Optional[str] = None) -> List[FileInMeca]:
        """Finds all files of the given type and optionally the given version."""
        def predicate(file: FileInMeca) -> bool:
            if file.type != file_type:
                return False
            if version is not None and file.version != version:
                return False
            return True

        return list(filter(predicate, self.files_in_manifest))

    def _get_file_of_type(self, file_type: str, version: Optional[str] = None) -> FileInMeca:
        """
        Finds the file of the given type and optionally the given version.

        If none or multiple matching files are found, a ValueError is raised.
        """
        files_of_type = self._get_files_of_type(file_type, version=version)
        num_files_found = len(files_of_type)
        if num_files_found < 1:
            raise ValueError(f'Found no file of type "{file_type}" and version "{version}"')
        if num_files_found > 1:
            raise ValueError(f'Found multiple files of type "{file_type}" and version "{version}"')
        return files_of_type[0]

    def get_xml(self, file_type: str, version: Optional[str] = None) -> Any:
        """
        Find the file of the given type and optionally the given version and parse it into an lxml.etree.Element.

        If none or multiple matching files are found, a ValueError is raised.
        """
        file = self._get_file_of_type(file_type, version=version)
        return self._parse_xml(file)
