"""
"""

__all__ = ["BatchDatabase", "DepositionAttempt", "ParsedFile"]

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    create_engine,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
    select,
    text,
)
from sqlalchemy.orm import registry, relationship, Session  # type: ignore[attr-defined] # it does have this attribute
from sqlalchemy.types import TypeDecorator
from typing import Any, List, Optional
from yaml import dump, load, Loader

from mecadoi.meca import Manuscript


mapper_registry = registry()


@dataclass
class ParsedFile:
    """A file that was parsed as a MECA archive."""

    path: str
    """The path that the file resided under when it was parsed. It's not guaranteed to still be there."""

    received_at: datetime
    """The time when the file was received."""

    manuscript: Optional[Manuscript] = None
    """
    The manuscript that was parsed from the file, if it was a valid MECA archive.

    Is None if parsing the file as a MECA archive failed.
    """

    doi: Optional[str] = None

    Valid = 1
    Invalid = 10
    NoDoi = 20
    NoReviews = 21
    Duplicate = 22
    status: Optional[int] = None

    id: Optional[int] = None
    """A unique identifier for this file."""

    def __repr__(self) -> str:
        return f"ParsedFile(id={self.id}, path={self.path}, doi={self.doi}, received_at={self.received_at})"


@dataclass
class DepositionAttempt:
    """An attempt for depositing DOIs for reviews in a MECA."""

    meca: ParsedFile
    """The MECA archive used in the attempt."""

    deposition: Optional[str] = None
    """The deposition XML generated for this attempt. Is None if this generation failed."""

    attempted_at: Optional[datetime] = None
    """The time when the deposition file was sent to the server."""

    Succeeded = 1
    DoisAlreadyPresent = 2
    Failed = 10
    VerificationFailed = 20
    GenerationFailed = 21
    status: Optional[int] = None

    verification_failed: Optional[bool] = None
    """Whether verifying the deposition file succeeded."""

    succeeded: Optional[bool] = None
    """Whether sending the deposition file succeeded. The deposition could still fail after processing!"""

    id: Optional[int] = None
    """A unique identifier for this attempt."""


@dataclass
class UsedDoi:
    doi: str
    resource: str
    claimed_at: datetime


class Yaml(TypeDecorator):  # type: ignore[type-arg]
    """An SQLAlchemy type for storing objects as YAML."""

    cache_ok = False
    impl = Text

    def process_bind_param(self, obj: Any, _: Any) -> Any:
        return dump(obj)

    def process_result_value(self, value: Any, _: Any) -> Any:
        if value:
            return load(value, Loader=Loader)
        else:
            return None


metadata = MetaData()

tbl_parsed_file = Table(
    "parsed_file",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("path", Text, nullable=False),
    Column("received_at", DateTime, nullable=False),
    Column("manuscript", Yaml, nullable=True),
    Column("doi", Text, nullable=True),
    Column("status", Integer, nullable=True),
)
mapper_registry.map_imperatively(ParsedFile, tbl_parsed_file)

tbl_deposition_attempt = Table(
    "deposition_attempt",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("id_parsed_file", ForeignKey("parsed_file.id")),
    Column("deposition", Text),
    Column("verification_failed", Boolean),
    Column("attempted_at", DateTime),
    Column("succeeded", Boolean),
    Column("status", Integer, nullable=True),
)
mapper_registry.map_imperatively(
    DepositionAttempt,
    tbl_deposition_attempt,
    properties={"meca": relationship(ParsedFile, lazy="joined")},
)

tbl_used_dois = Table(
    "used_dois",
    metadata,
    Column("doi", Text, primary_key=True),
    Column("resource", Text, nullable=False),
    Column("claimed_at", DateTime, nullable=False),
)
mapper_registry.map_imperatively(UsedDoi, tbl_used_dois)


class BatchDatabase:
    """An interface for the batch database storing information about processed MECAs and deposition attempts."""

    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url)

    def initialize(self) -> None:
        """Create all necessary tables. Does nothing if they already exist."""
        metadata.create_all(self.engine)

    def session(self) -> Session:
        return Session(self.engine)

    def insert_all(self, objects: Any) -> None:
        """Insert all given objects into the database."""
        with self.session() as session:  # type: ignore[attr-defined] # it does have this attribute
            with session.begin():
                # Deep-copying keeps the original objects transient, i.e. not associated with the database. Otherwise
                # SQLAlchemy's ORM kicks in and might raise errors if modifying the passed-in objects.
                session.add_all(deepcopy(objects))

    def _fetch_rows(self, statement: Any) -> Any:
        with self.session() as session:  # type: ignore[attr-defined] # it does have this attribute
            rows = session.execute(statement).all()
            return rows

    def fetch_all(self, clazz: Any) -> List[Any]:
        """Fetch all objects of the given type from the database."""
        statement = select(clazz)
        rows = self._fetch_rows(statement)
        return [row[0] for row in rows]

    def _fetch_parsed_files(self, statement: Any) -> List[ParsedFile]:
        return [row["ParsedFile"] for row in self._fetch_rows(statement)]

    def fetch_parsed_files_with_doi(self, doi: str) -> List[ParsedFile]:
        return self._fetch_parsed_files(
            select(ParsedFile).filter(ParsedFile.doi == doi)  # type: ignore
        )

    def fetch_parsed_files_between(
        self, after: datetime, before: datetime
    ) -> List[ParsedFile]:
        """Fetch all parsed files in the database between the given dates."""
        return self._fetch_parsed_files(
            select(ParsedFile)  # type: ignore
            .filter(
                ParsedFile.received_at > after,
                ParsedFile.received_at < before,
            )
            .order_by(ParsedFile.id)
        )

    def get_files_ready_for_deposition(
        self, after: datetime, before: datetime
    ) -> List[ParsedFile]:
        """Fetch all parsed files in the database that are ready to be deposited."""
        ids_parsed_files_with_deposition_attempt = select(DepositionAttempt.id_parsed_file)  # type: ignore
        return self._fetch_parsed_files(
            select(ParsedFile)  # type: ignore
            .filter(
                ParsedFile.received_at > after,
                ParsedFile.received_at < before,
                ParsedFile.id.not_in(ids_parsed_files_with_deposition_attempt),  # type: ignore
                ParsedFile.status == ParsedFile.Valid,
            )
            .order_by(ParsedFile.id)
        )

    def get_files_to_retry_deposition(
        self, after: datetime, before: datetime
    ) -> List[ParsedFile]:
        """Fetch all parsed files in the database that are ready to be deposited."""
        ids_parsed_files_with_failed_deposition_attempts = text(
            "SELECT id_parsed_file "
            "FROM ("
            "  SELECT id_parsed_file, MAX(attempted_at) "
            "  FROM deposition_attempt "
            "  GROUP BY id_parsed_file "
            f" HAVING status={DepositionAttempt.Failed} "
            f"     OR status={DepositionAttempt.VerificationFailed} "
            ")"
        )
        return self._fetch_parsed_files(
            select(ParsedFile)  # type: ignore
            .filter(
                ParsedFile.received_at > after,
                ParsedFile.received_at < before,
                ParsedFile.id.in_(ids_parsed_files_with_failed_deposition_attempts),  # type: ignore
            )
            .order_by(ParsedFile.id)
        )

    def mark_doi_as_used(self, doi: str, resource: str) -> None:
        used_doi = UsedDoi(doi=doi, resource=resource, claimed_at=datetime.now())
        with self.session() as session:  # type: ignore[attr-defined] # it does have this attribute
            with session.begin():
                session.add(deepcopy(used_doi))
