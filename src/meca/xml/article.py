from dataclasses import dataclass, field
from typing import List, Optional, Union
from .common import (
    ContribGroup,
    History,
)


@dataclass
class AbbrevJournalTitle:
    class Meta:
        name = "abbrev-journal-title"

    abbrev_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "abbrev-type",
            "type": "Attribute",
        }
    )


@dataclass
class Abstract:
    class Meta:
        name = "abstract"

    abstract_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "abstract-type",
            "type": "Attribute",
        }
    )
    p: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class ArticleId:
    class Meta:
        name = "article-id"

    pub_id_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "pub-id-type",
            "type": "Attribute",
        }
    )
    value: str = field(
        default=""
    )


@dataclass
class Corresp:
    class Meta:
        name = "corresp"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "label",
                    "type": str,
                },
                {
                    "name": "bold",
                    "type": str,
                },
                {
                    "name": "email",
                    "type": str,
                },
            ),
        }
    )


@dataclass
class CustomMeta:
    class Meta:
        name = "custom-meta"

    meta_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "meta-name",
            "type": "Element",
        }
    )
    meta_value: Optional[Union[str, int]] = field(
        default=None,
        metadata={
            "name": "meta-value",
            "type": "Element",
        }
    )


@dataclass
class Fn:
    class Meta:
        name = "fn"

    fn_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "fn-type",
            "type": "Attribute",
        }
    )
    p: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Issn:
    class Meta:
        name = "issn"

    pub_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "pub-type",
            "type": "Attribute",
        }
    )
    value: str = field(
        default=""
    )


@dataclass
class JournalId:
    class Meta:
        name = "journal-id"

    journal_id_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "journal-id-type",
            "type": "Attribute",
        }
    )
    value: str = field(
        default=""
    )


@dataclass
class KwdGroup:
    class Meta:
        name = "kwd-group"

    kwd: List[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Permissions:
    class Meta:
        name = "permissions"

    copyright_statement: Optional[object] = field(
        default=None,
        metadata={
            "name": "copyright-statement",
            "type": "Element",
        }
    )
    copyright_year: Optional[int] = field(
        default=None,
        metadata={
            "name": "copyright-year",
            "type": "Element",
        }
    )


@dataclass
class PubDate:
    class Meta:
        name = "pub-date"

    pub_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "pub-type",
            "type": "Attribute",
        }
    )


@dataclass
class SubjGroup:
    class Meta:
        name = "subj-group"

    subj_group_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "subj-group-type",
            "type": "Attribute",
        }
    )
    subject: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class TitleGroup:
    class Meta:
        name = "title-group"

    article_title: Optional[str] = field(
        default=None,
        metadata={
            "name": "article-title",
            "type": "Element",
        }
    )


@dataclass
class ArticleCategories:
    class Meta:
        name = "article-categories"

    subj_group: Optional[SubjGroup] = field(
        default=None,
        metadata={
            "name": "subj-group",
            "type": "Element",
        }
    )


@dataclass
class AuthorNotes:
    class Meta:
        name = "author-notes"

    corresp: Optional[Corresp] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    fn: Optional[Fn] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class CustomMetaGroup:
    class Meta:
        name = "custom-meta-group"

    custom_meta: List[CustomMeta] = field(
        default_factory=list,
        metadata={
            "name": "custom-meta",
            "type": "Element",
        }
    )


@dataclass
class JournalTitleGroup:
    class Meta:
        name = "journal-title-group"

    journal_title: Optional[str] = field(
        default=None,
        metadata={
            "name": "journal-title",
            "type": "Element",
        }
    )
    abbrev_journal_title: Optional[AbbrevJournalTitle] = field(
        default=None,
        metadata={
            "name": "abbrev-journal-title",
            "type": "Element",
        }
    )


@dataclass
class NamedContent:
    class Meta:
        name = "named-content"

    content_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "content-type",
            "type": "Attribute",
        }
    )
    value: str = field(
        default=""
    )


@dataclass
class FundingSource:
    class Meta:
        name = "funding-source"

    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "named-content",
                    "type": NamedContent,
                },
                {
                    "type": str,
                    "default": "",
                },
            ),
        }
    )


@dataclass
class AwardGroup:
    class Meta:
        name = "award-group"

    funding_source: Optional[FundingSource] = field(
        default=None,
        metadata={
            "name": "funding-source",
            "type": "Element",
        }
    )
    principal_award_recipient: Optional[str] = field(
        default=None,
        metadata={
            "name": "principal-award-recipient",
            "type": "Element",
        }
    )


@dataclass
class FundingGroup:
    class Meta:
        name = "funding-group"

    award_group: Optional[AwardGroup] = field(
        default=None,
        metadata={
            "name": "award-group",
            "type": "Element",
        }
    )


@dataclass
class ArticleMeta:
    class Meta:
        name = "article-meta"

    article_id: List[ArticleId] = field(
        default_factory=list,
        metadata={
            "name": "article-id",
            "type": "Element",
        }
    )
    article_categories: Optional[ArticleCategories] = field(
        default=None,
        metadata={
            "name": "article-categories",
            "type": "Element",
        }
    )
    title_group: Optional[TitleGroup] = field(
        default=None,
        metadata={
            "name": "title-group",
            "type": "Element",
        }
    )
    contrib_group: Optional[ContribGroup] = field(
        default=None,
        metadata={
            "name": "contrib-group",
            "type": "Element",
        }
    )
    author_notes: Optional[AuthorNotes] = field(
        default=None,
        metadata={
            "name": "author-notes",
            "type": "Element",
        }
    )
    pub_date: List[PubDate] = field(
        default_factory=list,
        metadata={
            "name": "pub-date",
            "type": "Element",
        }
    )
    elocation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "elocation-id",
            "type": "Element",
        }
    )
    history: Optional[History] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    permissions: Optional[Permissions] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    abstract: Optional[Abstract] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    kwd_group: Optional[KwdGroup] = field(
        default=None,
        metadata={
            "name": "kwd-group",
            "type": "Element",
        }
    )
    funding_group: Optional[FundingGroup] = field(
        default=None,
        metadata={
            "name": "funding-group",
            "type": "Element",
        }
    )
    custom_meta_group: Optional[CustomMetaGroup] = field(
        default=None,
        metadata={
            "name": "custom-meta-group",
            "type": "Element",
        }
    )


@dataclass
class JournalMeta:
    class Meta:
        name = "journal-meta"

    journal_id: Optional[JournalId] = field(
        default=None,
        metadata={
            "name": "journal-id",
            "type": "Element",
        }
    )
    journal_title_group: Optional[JournalTitleGroup] = field(
        default=None,
        metadata={
            "name": "journal-title-group",
            "type": "Element",
        }
    )
    issn: List[Issn] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Front:
    class Meta:
        name = "front"

    journal_meta: Optional[JournalMeta] = field(
        default=None,
        metadata={
            "name": "journal-meta",
            "type": "Element",
        }
    )
    article_meta: Optional[ArticleMeta] = field(
        default=None,
        metadata={
            "name": "article-meta",
            "type": "Element",
        }
    )


@dataclass
class Article:
    class Meta:
        name = "article"

    dtd_version: Optional[str] = field(
        default=None,
        metadata={
            "name": "dtd-version",
            "type": "Attribute",
        }
    )
    front: Optional[Front] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
