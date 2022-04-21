from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Metadata:
    class Meta:
        name = "metadata"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class ItemMetadata:
    class Meta:
        name = "item-metadata"

    metadata: List[Metadata] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Instance:
    class Meta:
        name = "instance"

    conversion: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    media_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "media-type",
            "type": "Attribute",
        }
    )
    origin: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class Item:
    class Meta:
        name = "item"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    version: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    file_order: Optional[int] = field(
        default=None,
        metadata={
            "name": "file-order",
            "type": "Element",
        }
    )
    item_metadata: Optional[ItemMetadata] = field(
        default=None,
        metadata={
            "name": "item-metadata",
            "type": "Element",
        }
    )
    instance: Optional[Instance] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Manifest:
    class Meta:
        name = "manifest"

    version: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    item: List[Item] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )
