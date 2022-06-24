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


class BatchDatabase:
    """
    Stores information about parsed MECA archives.

    Uses an sqlite3 file-based database whose path should be passed into the constructor. If no database exists at that
    path the constructor automatically initializes it.

    Complex objects like `Manuscript` are serialized before storage and deserialized after retrieval with yaml as the
    storage format.
    """

    CREATE_TABLE_STATEMENT = """CREATE TABLE IF NOT EXISTS parsed_file
    (
        path TEXT NOT NULL,
        received_at TIMESTAMP NOT NULL,
        manuscript TEXT,
        id INTEGER PRIMARY KEY
    )"""

    QUERY_INSERT_PARSED_FILES = (
        'INSERT INTO parsed_file (path, received_at, manuscript) '
        'VALUES (:path, :received_at, :manuscript)'
    )
    QUERY_SELECT_PARSED_FILES = 'SELECT path, received_at, manuscript, id FROM parsed_file'

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

    def get_all_parsed_files(self) -> List[ParsedFile]:
        """Fetch all parsed files in the database."""
        with self.conn() as conn:
            result = conn.execute(self.QUERY_SELECT_PARSED_FILES)
            return self._deserialize(result.fetchall())

    def initialize(self) -> None:
        """Create all necessary tables. Does nothing if they already exist."""
        with self.conn() as conn:
            conn.cursor().execute(self.CREATE_TABLE_STATEMENT)

    def _deserialize(self, result: List[Row]) -> List[ParsedFile]:
        return [
            ParsedFile(
                path=row['path'],
                received_at=datetime.fromisoformat(row['received_at']),
                manuscript=self._load(row['manuscript']),
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
