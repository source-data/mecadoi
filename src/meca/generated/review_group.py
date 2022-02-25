from dataclasses import dataclass, field
from typing import List, Optional, Union
from src.meca.generated.article import (
    AddrLine,
    Institution,
    Phone,
    Role,
)


@dataclass
class Date:
    class Meta:
        name = "date"

    date_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "date-type",
            "type": "Attribute",
        }
    )
    day: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    month: Optional[Union[int, str]] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    year: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Name:
    class Meta:
        name = "name"

    surname: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    given_names: Optional[str] = field(
        default=None,
        metadata={
            "name": "given-names",
            "type": "Element",
        }
    )
    prefix: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class ReviewItemQuestion:
    class Meta:
        name = "review-item-question"

    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    alt_title: Optional[str] = field(
        default=None,
        metadata={
            "name": "alt-title",
            "type": "Element",
        }
    )
    text: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class ReviewItemResponse:
    class Meta:
        name = "review-item-response"

    text: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Xref:
    class Meta:
        name = "xref"

    ref_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "ref-type",
            "type": "Attribute",
        }
    )
    rid: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class Aff:
    class Meta:
        name = "aff"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    institution: List[Union[str, Institution]] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )
    addr_line: List[AddrLine] = field(
        default_factory=list,
        metadata={
            "name": "addr-line",
            "type": "Element",
        }
    )
    country: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    phone: Optional[Phone] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    value: str = field(
        default=""
    )


@dataclass
class Contrib:
    class Meta:
        name = "contrib"

    contrib_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "contrib-type",
            "type": "Attribute",
        }
    )
    corresp: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    name: Optional[Name] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    email: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    role: Optional[Role] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    xref: Optional[Xref] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class History:
    class Meta:
        name = "history"

    date: List[Date] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class ReviewItem:
    class Meta:
        name = "review-item"

    is_confidential: Optional[str] = field(
        default=None,
        metadata={
            "name": "is-confidential",
            "type": "Attribute",
        }
    )
    review_item_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "review-item-type",
            "type": "Attribute",
        }
    )
    sequence_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "sequence-number",
            "type": "Attribute",
        }
    )
    review_item_question: Optional[ReviewItemQuestion] = field(
        default=None,
        metadata={
            "name": "review-item-question",
            "type": "Element",
        }
    )
    review_item_response: Optional[ReviewItemResponse] = field(
        default=None,
        metadata={
            "name": "review-item-response",
            "type": "Element",
        }
    )


@dataclass
class ContribGroup:
    class Meta:
        name = "contrib-group"

    contrib: List[Contrib] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )
    aff: List[Aff] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class ReviewItemGroup:
    class Meta:
        name = "review-item-group"

    review_item: List[ReviewItem] = field(
        default_factory=list,
        metadata={
            "name": "review-item",
            "type": "Element",
        }
    )


@dataclass
class Review:
    class Meta:
        name = "review"

    history: Optional[History] = field(
        default=None,
        metadata={
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
    review_item_group: Optional[ReviewItemGroup] = field(
        default=None,
        metadata={
            "name": "review-item-group",
            "type": "Element",
        }
    )


@dataclass
class Version:
    class Meta:
        name = "version"

    revision: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    review: List[Review] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class ReviewGroup:
    class Meta:
        name = "review-group"

    version: Optional[Version] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
