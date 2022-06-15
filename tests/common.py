"""Common functionality for the test cases."""

__all__ = ['MecaArchiveTestCase']

from os import listdir, mkdir
from os.path import isdir, isfile, join
import lxml.etree
from shutil import rmtree
from unittest import TestCase
from zipfile import ZipFile, ZIP_DEFLATED


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


class DepositionFileTestCase(TestCase):

    def assertDepositionFileEquals(self, expected_deposition_file: str, actual_deposition_file: str) -> None:
        ignore_namespaces = {
            'cr': 'http://www.crossref.org/schema/5.3.1',
        }
        ignore_xpaths = [
            './cr:head/cr:doi_batch_id',
            './cr:head/cr:timestamp',
        ]

        def canonicalize(xml_file: str) -> str:
            tree = lxml.etree.parse(xml_file)
            root = tree.getroot()
            for ignore_xpath in ignore_xpaths:
                for element_to_ignore in root.findall(ignore_xpath, namespaces=ignore_namespaces):
                    parent = element_to_ignore.getparent()
                    parent.remove(element_to_ignore)

            return lxml.etree.canonicalize(  # type: ignore[no-any-return]  # lxml docs say this does return a string
                xml_data=lxml.etree.tostring(root, encoding='unicode')
            )

        expected = canonicalize(expected_deposition_file)
        actual = canonicalize(actual_deposition_file)

        self.assertEqual(expected, actual)
