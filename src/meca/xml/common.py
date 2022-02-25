from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class AddrLine:
    class Meta:
        name = "addr-line"

    content_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "content-type",
            "type": "Attribute",
        }
    )
    value: Union[str, int] = field(
        default=""
    )


@dataclass
class Institution:
    class Meta:
        name = "institution"

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
class Phone:
    class Meta:
        name = "phone"

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
class ContribId:
    class Meta:
        name = "contrib-id"

    contrib_id_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "contrib-id-type",
            "type": "Attribute",
        }
    )
    specific_use: Optional[str] = field(
        default=None,
        metadata={
            "name": "specific-use",
            "type": "Attribute",
        }
    )
    value: str = field(
        default=""
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
class Role:
    class Meta:
        name = "role"

    content_type: Optional[int] = field(
        default=None,
        metadata={
            "name": "content-type",
            "type": "Attribute",
        }
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
    contrib_id: Optional[ContribId] = field(
        default=None,
        metadata={
            "name": "contrib-id",
            "type": "Element",
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
    day: Optional[Union[int, str]] = field(
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
class History:
    class Meta:
        name = "history"

    date: List[Date] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        }
    )
