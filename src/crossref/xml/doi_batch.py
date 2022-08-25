from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class InterWorkRelation:
    class Meta:
        name = "inter_work_relation"
        namespace = "http://www.crossref.org/relations.xsd"

    relationship_type: str = field(
        metadata={
            "name": "relationship-type",
            "type": "Attribute",
        }
    )
    identifier_type: str = field(
        metadata={
            "name": "identifier-type",
            "type": "Attribute",
        }
    )
    value: str = field(default="")


@dataclass
class Orcid:
    class Meta:
        name = "ORCID"
        namespace = "http://www.crossref.org/schema/5.3.1"

    authenticated: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    value: str = field(default="")


@dataclass
class Anonymous:
    class Meta:
        name = "anonymous"
        namespace = "http://www.crossref.org/schema/5.3.1"

    sequence: str = field(
        metadata={
            "type": "Attribute",
        }
    )
    contributor_role: str = field(
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class Depositor:
    class Meta:
        name = "depositor"
        namespace = "http://www.crossref.org/schema/5.3.1"

    depositor_name: str = field(
        metadata={
            "type": "Element",
        }
    )
    email_address: str = field(
        metadata={
            "type": "Element",
        }
    )


@dataclass
class DoiData:
    class Meta:
        name = "doi_data"
        namespace = "http://www.crossref.org/schema/5.3.1"

    doi: str = field(
        metadata={
            "type": "Element",
        }
    )
    resource: str = field(
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Institution:
    class Meta:
        name = "institution"
        namespace = "http://www.crossref.org/schema/5.3.1"

    institution_name: str = field(
        metadata={
            "type": "Element",
        }
    )


@dataclass
class ReviewDate:
    class Meta:
        name = "review_date"
        namespace = "http://www.crossref.org/schema/5.3.1"

    month: Union[int, str] = field(
        metadata={
            "type": "Element",
        }
    )
    day: Union[int, str] = field(
        metadata={
            "type": "Element",
        }
    )
    year: int = field(
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Titles:
    class Meta:
        name = "titles"
        namespace = "http://www.crossref.org/schema/5.3.1"

    title: str = field(
        metadata={
            "type": "Element",
        }
    )


@dataclass
class RelatedItem:
    class Meta:
        name = "related_item"
        namespace = "http://www.crossref.org/relations.xsd"

    inter_work_relation: InterWorkRelation = field(
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Affiliations:
    class Meta:
        name = "affiliations"
        namespace = "http://www.crossref.org/schema/5.3.1"

    institution: Institution = field(
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Head:
    class Meta:
        name = "head"
        namespace = "http://www.crossref.org/schema/5.3.1"

    doi_batch_id: str = field(
        metadata={
            "type": "Element",
        }
    )
    timestamp: int = field(
        metadata={
            "type": "Element",
        }
    )
    depositor: Depositor = field(
        metadata={
            "type": "Element",
        }
    )
    registrant: str = field(
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Program:
    class Meta:
        name = "program"
        namespace = "http://www.crossref.org/relations.xsd"

    related_item: List[RelatedItem] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class PersonName:
    class Meta:
        name = "person_name"
        namespace = "http://www.crossref.org/schema/5.3.1"

    sequence: str = field(
        metadata={
            "type": "Attribute",
        }
    )
    given_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    surname: Optional[str] = field(
        default="Surname",
        metadata={
            "type": "Element",
        },
    )
    contributor_role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    affiliations: Optional[Affiliations] = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    orcid: Optional[Orcid] = field(
        default=None,
        metadata={
            "name": "ORCID",
            "type": "Element",
        },
    )


@dataclass
class Contributors:
    class Meta:
        name = "contributors"
        namespace = "http://www.crossref.org/schema/5.3.1"

    anonymous: Optional[Anonymous] = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    person_name: List[PersonName] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class PeerReview:
    class Meta:
        name = "peer_review"
        namespace = "http://www.crossref.org/schema/5.3.1"

    revision_round: int = field(
        metadata={
            "name": "revision-round",
            "type": "Attribute",
        }
    )
    type: str = field(
        metadata={
            "type": "Attribute",
        }
    )
    contributors: Contributors = field(
        metadata={
            "type": "Element",
        }
    )
    titles: Titles = field(
        metadata={
            "type": "Element",
        }
    )
    review_date: ReviewDate = field(
        metadata={
            "type": "Element",
        }
    )
    institution: Institution = field(
        metadata={
            "type": "Element",
        }
    )
    running_number: str = field(
        metadata={
            "type": "Element",
        }
    )
    program: Program = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.crossref.org/relations.xsd",
        }
    )
    doi_data: DoiData = field(
        metadata={
            "type": "Element",
        }
    )
    stage: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class Body:
    class Meta:
        name = "body"
        namespace = "http://www.crossref.org/schema/5.3.1"

    peer_review: List[PeerReview] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class DoiBatch:
    class Meta:
        name = "doi_batch"
        namespace = "http://www.crossref.org/schema/5.3.1"

    version: str = field(
        metadata={
            "type": "Attribute",
        }
    )
    schema_location: str = field(
        metadata={
            "name": "schemaLocation",
            "type": "Attribute",
            "namespace": "http://www.w3.org/2001/XMLSchema-instance",
        }
    )
    head: Head = field(
        metadata={
            "type": "Element",
        }
    )
    body: Body = field(
        metadata={
            "type": "Element",
        }
    )
