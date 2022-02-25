from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContactName:
    class Meta:
        name = "contact-name"

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


@dataclass
class ProcessingInstructions:
    class Meta:
        name = "processing-instructions"

    comments: Optional[object] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Contact:
    class Meta:
        name = "contact"

    role: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    contact_name: Optional[ContactName] = field(
        default=None,
        metadata={
            "name": "contact-name",
            "type": "Element",
        }
    )
    email: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    phone: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Publication:
    class Meta:
        name = "publication"

    type: Optional[str] = field(
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
    acronym: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    contact: Optional[Contact] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class ServiceProvider:
    class Meta:
        name = "service-provider"

    provider_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "provider-name",
            "type": "Element",
        }
    )
    contact: Optional[Contact] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Destination:
    class Meta:
        name = "destination"

    service_provider: Optional[ServiceProvider] = field(
        default=None,
        metadata={
            "name": "service-provider",
            "type": "Element",
        }
    )
    publication: Optional[Publication] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Source:
    class Meta:
        name = "source"

    service_provider: Optional[ServiceProvider] = field(
        default=None,
        metadata={
            "name": "service-provider",
            "type": "Element",
        }
    )
    publication: Optional[Publication] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class Transfer:
    class Meta:
        name = "transfer"

    version: Optional[float] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )
    source: Optional[Source] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    destination: Optional[Destination] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    processing_instructions: Optional[ProcessingInstructions] = field(
        default=None,
        metadata={
            "name": "processing-instructions",
            "type": "Element",
        }
    )
