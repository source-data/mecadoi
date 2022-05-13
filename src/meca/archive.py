from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import lxml.etree
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union, cast
from xsdata.formats.dataclass.parsers import XmlParser
from zipfile import ZipFile

from src.meca.xml.common import Aff, Contrib, ContribGroup
from .xml.article import Article
from .xml.manifest import Manifest
from .xml.review_group import ReviewGroup, Review
from .xml.transfer import Transfer


T = TypeVar('T')


class MECArchive:
    """
    Read metadata from a MECA archive.

    To get started, pass a ZipFile to the constructor of this class: `meca = MECArchive(zip_file)`. This reads all
    metadata from the archive's XML files into the new  instance's `article`, `manifest`, `transfer`, and `reviews`
    attributes. For the structure of these objects, see their respective file in the `.xml` module.
    A few commonly accessed attributes are also set on the new instance: the title, DOI, copyright year, and journal of
    the article within the archive.

    """
    class MECAdata:
        """Describes a metadata file within a MECA archive."""
        def __init__(self, filename: str, data_class: Type[T], validation_schema: Optional[str] = None) -> None:
            self.filename = filename
            self.data_class = data_class
            self.validation_schema = validation_schema

    ARTICLE = MECAdata('article.xml', Article)
    MANIFEST = MECAdata('manifest.xml', Manifest, validation_schema='schemas/meca/manifest.dtd')
    REVIEWS = MECAdata('reviews.xml', ReviewGroup, validation_schema='schemas/meca/reviews.dtd')
    TRANSFER = MECAdata('transfer.xml', Transfer, validation_schema='schemas/meca/transfer.dtd')

    REQUIRED_FILES = [ARTICLE, MANIFEST, TRANSFER]
    METADATA_FILES = REQUIRED_FILES + [REVIEWS]

    def __init__(self, path_to_archive: Union[str, Path], strict_validation: bool = False) -> None:
        with ZipFile(path_to_archive, 'r') as archive:
            self._files_in_archive = archive.namelist()

            is_valid, reason = self.is_valid(archive, strict=strict_validation)
            if not is_valid:
                raise ValueError(f'not a valid MECA archive: {reason}')

            def parse(meca_data: MECArchive.MECAdata) -> T:
                if not self.is_present(meca_data):
                    raise ValueError(f'{meca_data.filename} not found in MECA archive')
                parser = XmlParser()
                with archive.open(meca_data.filename) as xml_file:
                    return parser.parse(xml_file, clazz=meca_data.data_class)

            article = parse(MECArchive.ARTICLE)  # type: Article
            manifest = parse(MECArchive.MANIFEST)  # type: Manifest
            transfer = parse(MECArchive.TRANSFER)  # type: Transfer
            try:
                reviews = parse(MECArchive.REVIEWS)  # type: Optional[ReviewGroup]
            except ValueError:
                reviews = None

        self.article = article
        self.manifest = manifest
        self.transfer = transfer
        self.reviews = reviews

        self.article_title = article.front.article_meta.title_group.article_title
        self.journal_title = (
            article.front.journal_meta.journal_title_group.journal_title
            if article.front.journal_meta.journal_title_group
            else None
        )
        self.copyright_year = (
            article.front.article_meta.permissions.copyright_year
            if article.front.article_meta.permissions
            else None
        )
        self.article_doi = get_el_with_attr(article.front.article_meta.article_id, 'pub_id_type', 'doi').value

        preprint_doi = None
        if self.article.front.article_meta.custom_meta_group:
            for custom_meta_tag in self.article.front.article_meta.custom_meta_group.custom_meta:
                tag_name = custom_meta_tag.meta_name
                if tag_name == "Pre-existing BioRxiv Preprint DOI":
                    preprint_doi = str(custom_meta_tag.meta_value)
        self.article_preprint_doi = preprint_doi

        self.revision_rounds = [
            RevisionRoundInfo(
                revision=revision_round.revision,
                reviews=[
                    ReviewInfo(
                        running_number=running_number,
                        date_assigned=assigned_date(meca_review),
                        date_completed=get_date('completed', meca_review),
                        contributors=', '.join([
                            f'{contrib.name.surname}, {contrib.name.given_names}'
                            for contrib in meca_review.contrib_group.contrib
                            if contrib.name
                        ]) if meca_review.contrib_group else 'Unknown',
                        text={
                            review_item.review_item_question.title: review_item.review_item_response.text
                            for review_item in meca_review.review_item_group.review_item
                            if (
                                review_item.review_item_question
                                and review_item.review_item_question.title
                                and review_item.review_item_response
                                and review_item.review_item_response.text
                            )
                        } if meca_review.review_item_group else {},
                    )
                    for running_number, meca_review in enumerate(
                        sorted(revision_round.review, key=assigned_date),
                        start=1
                    )
                ],
                author_reply=(
                    AuthorReplyInfo(
                        contributors=[
                            AuthorInfo(
                                given_name=(
                                    contrib.name.given_names if contrib.name and contrib.name.given_names else ''
                                ),
                                surname=contrib.name.surname if contrib.name and contrib.name.surname else '',
                                orcid=OrcidInfo(
                                    id=contrib.contrib_id.value,
                                    is_authenticated=contrib.contrib_id.specific_use == 'authenticated',
                                ) if contrib.contrib_id and contrib.contrib_id.contrib_id_type == 'orcid' else None,
                                affiliation=get_affiliation(contrib, self.article.front.article_meta.contrib_group),
                                is_corresponding=contrib.corresp is not None and contrib.corresp == 'yes',
                            )
                            for contrib in self.article.front.article_meta.contrib_group.contrib
                            if contrib.contrib_type == 'author'
                        ] if self.article.front.article_meta.contrib_group else []
                    )
                    if len(
                        [
                            item for item in self.manifest.item
                            if item.type == 'Response to Reviewers' and item.version == revision_round.revision
                        ]
                    ) == 1
                    else None
                ),
            )
            for revision_round in self.reviews.version
        ] if self.reviews else []

    def is_valid(self, archive: ZipFile, strict: bool = False) -> Tuple[bool, str]:
        """
        Is this MECA archive valid?

        Checks if the given archive file is a valid ZIP file and that all required metadata files are present. If
        `strict=True` is passed, all metadata files (excluding article.xml) are validated against their schema
        definitions.
        """
        # check that the ZIP archive is valid
        first_bad_file = archive.testzip()
        if first_bad_file:
            return False, f'ZIP archive is invalid, first bad file: {first_bad_file}'

        # check that the MECA archive has all required files
        missing_required_files = []
        for required_file in MECArchive.REQUIRED_FILES:
            if not self.is_present(required_file):
                missing_required_files.append(required_file.filename)
        if missing_required_files:
            return False, f'MECA archive is missing these required files: {", ".join(missing_required_files)}'

        if strict:
            # validate the MECA files according to their schema
            invalid_files = []
            for meca_data in MECArchive.METADATA_FILES:
                schema_file = meca_data.validation_schema
                if not schema_file:
                    continue

                if schema_file.endswith('.xsd'):
                    xml_schema = lxml.etree.XMLSchema(
                        lxml.etree.parse(schema_file)
                    )
                elif schema_file.endswith('.dtd'):
                    xml_schema = lxml.etree.DTD(schema_file)
                else:
                    raise ValueError(f'no lxml validator class found for schema file {schema_file}')

                with archive.open(meca_data.filename) as xml_file:
                    xml_doc = lxml.etree.parse(xml_file)
                    try:
                        xml_schema.assertValid(xml_doc)
                    except lxml.etree.DocumentInvalid as e:
                        invalid_files.append((meca_data.filename, e))
            if invalid_files:
                output = ''
                for invalid_filename, assertion_error in invalid_files:
                    output += f'''{invalid_filename}: {assertion_error.args}
'''
                return False, output

        return True, ''

    def is_present(self, meca_data: MECAdata) -> bool:
        """Is the given metadata file present in this MECA archive?"""
        return meca_data.filename in self._files_in_archive

    def __str__(self) -> str:
        return f'''
{self.article_title}
Article DOI: {self.article_doi}
Preprint DOI: {self.article_preprint_doi if self.article_preprint_doi else "-"}
{self.journal_title}, {self.copyright_year}
'''.strip()

    def __repr__(self) -> str:
        return self.__str__()


def get_affiliation(contrib: Contrib, contrib_group: ContribGroup) -> Optional[str]:
    if not (contrib.xref and contrib.xref.rid):
        return None
    affiliation = cast(Aff, get_el_with_attr(contrib_group.aff, 'id', contrib.xref.rid))
    if not (affiliation and affiliation.institution):
        return None
    institution = affiliation.institution[0]
    try:
        institution_name = institution.value  # type: ignore[union-attr] # handled by try clause
    except AttributeError:
        institution_name = institution
    return str(institution_name)


def get_el_with_attr(elements: List[Any], attr: str, val: str) -> Any:
    """
    Returns the first of the given elements that has the given attribute with the given value.

    Use it like so to get the element that holds the article's DOI:
    `get_el_with_attr(meca_archive.article.front.article_meta.article_id, 'pub_id_type', 'doi')`
    """
    el = [el for el in elements if getattr(el, attr) == val]
    return el[0] if el else None


def assigned_date(meca_review: Review) -> datetime:
    return get_date('assigned', meca_review)


def get_date(date_type: str, meca_review: Review) -> datetime:
    if meca_review.history:
        date = get_el_with_attr(meca_review.history.date, 'date_type', date_type)
        if date:
            return datetime(date.year, date.month, date.day)
    return datetime.min  # return the lowest possible value for reviews with unknown history or date


@dataclass
class OrcidInfo:
    id: str
    is_authenticated: bool


@dataclass
class AuthorInfo:
    given_name: str
    surname: str
    orcid: Optional[OrcidInfo]
    affiliation: Optional[str]
    is_corresponding: bool


@dataclass
class AuthorReplyInfo:
    contributors: List[AuthorInfo]


@dataclass
class ReviewInfo:
    running_number: int
    date_assigned: datetime
    date_completed: datetime
    contributors: str
    text: Dict[str, str]


@dataclass
class RevisionRoundInfo:
    revision: Optional[int]
    reviews: List[ReviewInfo]
    author_reply: Optional[AuthorReplyInfo]
