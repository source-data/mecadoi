from io import StringIO
from importlib import reload
from pathlib import Path
from typing import cast
from unittest.mock import patch
import alembic.config
import sys

from mecadoi.config import DB_URL
from tests.test_db import BatchDbTestCase


class DatabaseTestCase(BatchDbTestCase):
    def get_db_file(self) -> str:
        return "tests/tmp/batch/batch.sqlite3"

    def setUp(self) -> None:
        self.assertEqual(self.get_db_url(), DB_URL)
        super().setUp()
        self.migrations = [
            migration_file.stem.split("_")[0]
            for migration_file in Path("mecadoi/migrations/versions").glob("*.py")
            if migration_file.stem != "__init__"
        ]

    def migrate_to(self, revision: str) -> None:
        command_line_args = ["upgrade", revision]
        alembic.config.CommandLine().main(argv=command_line_args)  # type: ignore[no-untyped-call]

    def get_current_db_revision(self) -> str:
        with patch("sys.stdout", new_callable=StringIO) as stdout_mock:
            reload(alembic.config)
            self.assertEqual(StringIO, type(sys.stdout))

            alembic.config.CommandLine().main(argv=["current"])  # type: ignore[no-untyped-call]
            command_output = cast("StringIO", stdout_mock).getvalue()
            current_revision = command_output.strip().removesuffix(" (head)")

        reload(alembic.config)
        self.assertNotEqual(StringIO, type(sys.stdout))

        return current_revision

    def test_migrate(self) -> None:
        for target_revision in self.migrations:
            with self.subTest(target_revision=target_revision):
                self.clear_database()
                self.assertEqual("", self.get_current_db_revision())
                self.migrate_to(target_revision)
                self.assertEqual(target_revision, self.get_current_db_revision())
