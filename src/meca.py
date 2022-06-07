""""""

__all__ = ['parse_meca_archive']

from dataclasses import dataclass
from datetime import datetime
from html import unescape
from lxml.etree import parse, tostring
from pathlib import Path
from typing import IO, Any, List, Optional, Set, Union
from zipfile import ZipFile

from src.model import Article, Author, AuthorReply, Orcid, Review, RevisionRound


def parse_meca_archive(path_to_archive: Union[str, Path], use_preprint_doi: bool = True) -> Article:
    """Read the MECA archive at the given path and construct an Article from it."""

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
    return Article(
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

    To get started, pass a zipfile.ZipFile to the constructor of this class: `meca = MECArchive(zip_file)`.
    """

    _MEDIA_TYPE_XML = 'application/xml'

    MANIFEST = 'manifest'
    TRANSFER = 'transfer-metadata'
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
        return ZipFile(self.path_to_archive, 'r')

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
            raise ValueError('Found no file of type "{file_type}" and version "{version}"')
        if num_files_found > 1:
            raise ValueError('Found multiple files of type "{file_type}" and version "{version}"')
        return files_of_type[0]

    def get_xml(self, file_type: str, version: Optional[str] = None) -> Any:
        """
        Find the file of the given type and optionally the given version and parse it into an lxml.etree.Element.

        If none or multiple matching files are found, a ValueError is raised.
        """
        file = self._get_file_of_type(file_type, version=version)
        return self._parse_xml(file)
