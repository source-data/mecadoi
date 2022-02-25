from dataclasses import dataclass, field
from typing import List, Optional, Union
from .common import (
    ContribGroup,
    History,
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

    version: List[Version] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )
