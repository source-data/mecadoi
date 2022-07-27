"""Common functionality for the test cases."""

__all__ = ['MecaArchiveTestCase']

from os import listdir, mkdir
from os.path import isdir, isfile, join
from typing import List, Tuple
from shutil import rmtree
from unittest import TestCase
from xsdata.formats.dataclass.parsers import XmlParser
from zipfile import ZipFile, ZIP_DEFLATED

from src.crossref.xml import DoiBatch


def _add_to_zip(zf: ZipFile, path: str, zip_path: str) -> None:
    if isfile(path):
        zf.write(path, zip_path, ZIP_DEFLATED)
    elif isdir(path):
        if zip_path:
            zf.write(path, zip_path)
        for nm in sorted(listdir(path)):
            _add_to_zip(zf, join(path, nm), join(zip_path, nm))
    else:
        # ignore
        pass


def create_zip(zip_name: str, dir: str) -> None:
    """Create a zip file at the path `zip_name` that contains all files within `dir`."""
    with ZipFile(zip_name, 'w') as zf:
        _add_to_zip(zf, dir, '')


class MecaArchiveTestCase(TestCase):
    """
    A unittest.TestCase that creates zip archives from all directories in the MECA resource directory.

    In the TestCase.setUp() method, i.e. before each test method is called, the directory MECA_TARGET_DIR is deleted
    and recreated. Then, for each source directory inside MECA_SOURCE_DIR, a zip file is created inside MECA_TARGET_DIR
    that contains all files inside the source directory.
    """

    MECA_SOURCE_DIR = 'tests/resources/meca'
    MECA_TARGET_DIR = 'tests/tmp/meca'

    def setUp(self) -> None:
        try:
            rmtree(self.MECA_TARGET_DIR)
        except FileNotFoundError:
            pass
        mkdir(self.MECA_TARGET_DIR)

        self.meca_archives = []
        for meca_source in listdir(self.MECA_SOURCE_DIR):
            file_path = f'{self.MECA_SOURCE_DIR}/{meca_source}'
            if isdir(file_path):
                zip_path = self.get_meca_archive_path(meca_source)
                create_zip(zip_path, file_path)
                self.meca_archives.append(zip_path)

        return super().setUp()

    def get_meca_archive_path(self, meca_name: str) -> str:
        return f'{self.MECA_TARGET_DIR}/{meca_name}.zip'

    def get_meca_archive_paths(self, meca_names: List[str]) -> List[str]:
        return [self.get_meca_archive_path(meca_name) for meca_name in meca_names]


class DepositionFileTestCase(TestCase):

    def assertDepositionFileEquals(self, expected_deposition_file: str, actual_deposition_file: str) -> None:
        def parse(xml_file: str) -> Tuple[DoiBatch, str, int]:
            parser = XmlParser()
            doi_batch = parser.from_string(xml_file, DoiBatch)
            doi_batch_id = doi_batch.head.doi_batch_id
            timestamp = doi_batch.head.timestamp

            doi_batch.head.doi_batch_id = "doi_batch_id"
            doi_batch.head.timestamp = 1234

            return doi_batch, doi_batch_id, timestamp

        expected_doi_batch, _, _ = parse(expected_deposition_file)
        actual_doi_batch, actual_id, actual_timestamp = parse(actual_deposition_file)

        self.assertEqual(expected_doi_batch, actual_doi_batch)
        self.assertIsNotNone(actual_id)
        self.assertIsNotNone(actual_timestamp)
