"""

"""
from dataclasses import dataclass
from datetime import datetime
from sqlite3 import Connection, Row, connect
from typing import Any, List, Optional, cast

from yaml import dump, load, Loader

from src.meca import Manuscript


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

    id: Optional[int] = None
    """A unique identifier for this file."""


@dataclass
class DepositionAttempt:

    meca: ParsedFile

    deposition: Optional[str] = None

    attempted_at: Optional[datetime] = None

    succeeded: Optional[bool] = None

    id: Optional[int] = None


class BatchDatabase:
    """
    Stores information about parsed MECA archives.

    Uses an sqlite3 file-based database whose path should be passed into the constructor. If no database exists at that
    path the constructor automatically initializes it.

    Complex objects like `Manuscript` are serialized before storage and deserialized after retrieval with yaml as the
    storage format.
    """

    CREATE_TABLE_STATEMENTS = [
        (
            'CREATE TABLE IF NOT EXISTS parsed_file ('
            '  path TEXT NOT NULL,'
            '  received_at TIMESTAMP NOT NULL,'
            '  manuscript TEXT,'
            '  id INTEGER PRIMARY KEY'
            ')'
        ),
        (
            'CREATE TABLE IF NOT EXISTS deposition_attempt ('
            '  id_parsed_file INTEGER NOT NULL,'
            '  deposition TEXT,'
            '  attempted_at TIMESTAMP,'
            '  succeeded BOOLEAN,'
            '  id INTEGER PRIMARY KEY,'
            '  FOREIGN KEY(id_parsed_file) REFERENCES parsed_file(id)'
            ')'
        ),
    ]

    QUERY_INSERT_PARSED_FILES = (
        'INSERT INTO parsed_file (path, received_at, manuscript) '
        'VALUES (:path, :received_at, :manuscript)'
    )
    QUERY_SELECT_PARSED_FILES = (
        'SELECT p.path, p.received_at, p.manuscript, p.id '
        'FROM parsed_file AS p '
        'WHERE p.received_at > :after AND p.received_at < :before'
    )
    QUERY_SELECT_PARSED_FILES_WITH_MANUSCRIPT_AND_WITHOUT_ATTEMPTS = (
        'SELECT p.path, p.received_at, p.manuscript, p.id '
        'FROM parsed_file AS p '
        'WHERE p.manuscript IS NOT NULL AND p.id NOT IN (SELECT id_parsed_file from deposition_attempt) '
        'AND p.received_at > :after AND p.received_at < :before'
    )
    QUERY_SELECT_PARSED_FILES_WITH_ONLY_FAILED_ATTEMPTS = (
        'SELECT p.path, p.received_at, p.manuscript, p.id '
        'FROM parsed_file AS p '
        '  LEFT JOIN deposition_attempt AS d ON p.id = d.id_parsed_file '
        'WHERE p.manuscript IS NOT NULL '
        'GROUP BY p.id HAVING SUM(d.succeeded) = 0'
    )
    QUERY_INSERT_DEPOSITION_ATTEMPTS = (
        'INSERT INTO deposition_attempt (deposition, attempted_at, succeeded, id_parsed_file) '
        'VALUES (:deposition, :attempted_at, :succeeded, :id_parsed_file)'
    )
    QUERY_SELECT_DEPOSITION_ATTEMPTS = (
        'SELECT d.id, d.deposition, d.attempted_at, d.succeeded, d.id_parsed_file, p.path, p.received_at, p.manuscript '
        'FROM deposition_attempt AS d LEFT JOIN parsed_file AS p ON d.id_parsed_file = p.id'
    )

    def __init__(self, db_file: str) -> None:
        self.db_file = db_file
        self.initialize()

    def conn(self) -> Connection:
        connection = connect(self.db_file)
        connection.row_factory = Row
        return connection

    def add_parsed_files(self, parsed_files: List[ParsedFile]) -> None:
        """Add the given files to the database."""
        with self.conn() as conn:
            params = [
                {
                    'path': parsed_file.path,
                    'received_at': parsed_file.received_at,
                    'manuscript': self._dump(parsed_file.manuscript),
                }
                for parsed_file in parsed_files
            ]
            conn.executemany(self.QUERY_INSERT_PARSED_FILES, params)

    def with_date_filter(
        self,
        query: str,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
    ) -> List[ParsedFile]:
        params = {
            "after": datetime(1, 1, 1) if after is None else after,
            "before": datetime.now() if before is None else before,
        }
        with self.conn() as conn:
            result = conn.execute(query, params)
            return self._deserialize_parsed_files(result.fetchall())

    def get_all_parsed_files(
        self,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
    ) -> List[ParsedFile]:
        """Fetch all parsed files in the database."""
        return self.with_date_filter(self.QUERY_SELECT_PARSED_FILES, after=after, before=before)

    def add_deposition_attempts(self, deposition_attempts: List[DepositionAttempt]) -> None:
        """Add the given deposition attempts to the database."""
        with self.conn() as conn:
            params = [
                {
                    'deposition': deposition_attempt.deposition,
                    'attempted_at': deposition_attempt.attempted_at,
                    'succeeded': deposition_attempt.succeeded,
                    'id_parsed_file': deposition_attempt.meca.id,
                }
                for deposition_attempt in deposition_attempts
            ]
            conn.executemany(self.QUERY_INSERT_DEPOSITION_ATTEMPTS, params)

    def get_all_deposition_attempts(self) -> List[DepositionAttempt]:
        """Fetch all deposition attempts in the database."""
        with self.conn() as conn:
            result = conn.execute(self.QUERY_SELECT_DEPOSITION_ATTEMPTS)
            return self._deserialize_deposition_attempts(result.fetchall())

    def get_files_ready_for_deposition(
        self,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None
    ) -> List[ParsedFile]:
        parsed_files = self.with_date_filter(
            self.QUERY_SELECT_PARSED_FILES_WITH_MANUSCRIPT_AND_WITHOUT_ATTEMPTS, after=after, before=before)
        return [
            p for p in parsed_files
            if p.manuscript and p.manuscript.preprint_doi and p.manuscript.review_process
        ]

    def initialize(self) -> None:
        """Create all necessary tables. Does nothing if they already exist."""
        with self.conn() as conn:
            for statement in self.CREATE_TABLE_STATEMENTS:
                conn.execute(statement)

    def _deserialize_parsed_files(self, result: List[Row]) -> List[ParsedFile]:
        return [
            ParsedFile(
                path=row['path'],
                received_at=datetime.fromisoformat(row['received_at']),
                manuscript=self._load(row['manuscript']),
                id=row['id'],
            )
            for row in result
        ]

    def _deserialize_deposition_attempts(self, result: List[Row]) -> List[DepositionAttempt]:
        return [
            DepositionAttempt(
                deposition=row['deposition'],
                attempted_at=datetime.fromisoformat(row['attempted_at']) if row['attempted_at'] else None,
                succeeded=None if row['succeeded'] is None else bool(row['succeeded']),
                meca=ParsedFile(
                    path=row['path'],
                    received_at=datetime.fromisoformat(row['received_at']),
                    manuscript=self._load(row['manuscript']),
                    id=row['id_parsed_file'],
                ),
                id=row['id'],
            )
            for row in result
        ]

    def _dump(self, obj: Any) -> Optional[str]:
        if obj is None:
            return None
        return cast(str, dump(obj))

    def _load(self, obj_str: Optional[str]) -> Any:
        if obj_str is None:
            return None
        return load(obj_str, Loader=Loader)
