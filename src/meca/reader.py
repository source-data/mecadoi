from pathlib import Path

from bs4 import BeautifulSoup
from lxml import etree
from typing import Tuple
from zipfile import ZipFile


class MECArchive:

    class MECAdata:
        def __init__(self, filename, validation_schema=None) -> None:
            self.filename = filename
            self.validation_schema = validation_schema

    MANIFEST = MECAdata('manifest.xml', validation_schema='schemas/meca/manifest.dtd')
    ARTICLE = MECAdata('article.xml')
    TRANSFER = MECAdata('transfer.xml', validation_schema='schemas/meca/transfer.dtd')
    REVIEWS = MECAdata('reviews.xml', validation_schema='schemas/meca/reviews.dtd')

    REQUIRED_FILES = [MANIFEST, ARTICLE, TRANSFER]
    METADATA_FILES = REQUIRED_FILES + [REVIEWS]

    class ArchiveInfo:
        def __init__(self, article_title=None, journal_title=None, doi=None, copyright_year=None, authors=None, num_reviews=0) -> None:
            self.article_title = article_title
            self.journal_title = journal_title
            self.doi = doi
            self.copyright_year = copyright_year
            self.authors = authors
            self.num_reviews = num_reviews

    def __init__(self, archive: ZipFile, strict_validation=False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._archive = archive
        self._files_in_archive = self._archive.namelist()

        is_valid, reason = self.is_valid(strict=strict_validation)
        if not is_valid:
            raise ValueError(f'Not a valid MECA archive: {reason}')

        self._metadata = {}
        self.info = self.parse_archive_for_info()

    def is_valid(self, strict=False) -> Tuple[bool, str]:
        # check that the ZIP archive is valid
        first_bad_file = self._archive.testzip()
        if first_bad_file:
            return False, f'ZIP archive is invalid, first bad file: {first_bad_file}'

        # check that the MECA archive has all required files
        missing_required_files = []
        for required_file in MECArchive.REQUIRED_FILES:
            if not self._is_present(required_file):
                missing_required_files.append(required_file.filename)
        if missing_required_files:
            return False, f'MECA archive is missing these required files: {", ".join(missing_required_files)}'

        if strict:
            # validate the MECA files according to their schema
            invalid_files = []
            for meca_data in MECArchive.METADATA_FILES:
                schema_file = meca_data.validation_schema
                print(schema_file)
                if not schema_file:
                    continue

                if schema_file.endswith('.xsd'):
                    xml_schema = etree.XMLSchema(
                        etree.parse(schema_file)
                    )
                elif schema_file.endswith('.dtd'):
                    xml_schema = etree.DTD(schema_file)
                else:
                    raise ValueError(f'No lxml validator class found for schema file {schema_file}')

                with self._open_file_in_archive(meca_data) as xml_file:
                    xml_doc = etree.parse(xml_file)
                    try:
                        xml_schema.assertValid(xml_doc)
                    except etree.DocumentInvalid as e:
                        invalid_files.append((meca_data.filename, e))
            if invalid_files:
                output = ''
                for invalid_filename, assertion_error in invalid_files:
                    output += f'''{invalid_filename}: {assertion_error.args}
'''
                return False, output

        return True, ''

    def _is_present(self, meca_data: MECAdata):
        return meca_data.filename in self._files_in_archive

    def _open_file_in_archive(self, meca_data: MECAdata):
        return self._archive.open(meca_data.filename)

    def _parse_file(self, meca_data: MECAdata):
        filename = meca_data.filename
        if not (filename in self._metadata):
            with self._open_file_in_archive(meca_data) as xml_file:
                self._metadata[filename] = BeautifulSoup(xml_file, 'xml')

        return self._metadata[filename]

    def parse_archive_for_info(self) -> None:
        archive_info = MECArchive.ArchiveInfo()

        def _get_tag_text(soup, *args, **kwargs):
            tag = soup.find(*args, **kwargs)
            if tag:
                return tag.string.strip()

        article_info = self._parse_file(MECArchive.ARTICLE)

        archive_info.article_title = _get_tag_text(article_info, 'article-title')
        archive_info.journal_title = _get_tag_text(article_info, 'journal-title')
        archive_info.doi = _get_tag_text(article_info, 'article-id', attrs={'pub-id-type': 'doi'})
        archive_info.copyright_year = _get_tag_text(article_info, 'copyright-year')
        archive_info.authors = ' and '.join([
            f'{author.find("surname").string}, {author.find("given-names").string}'.strip()
            for author in article_info.find_all('contrib', attrs={'contrib-type': 'author'})
        ])

        if self._is_present(MECArchive.REVIEWS):
            reviews_info = self._parse_file(MECArchive.REVIEWS)
            archive_info.num_reviews = len(reviews_info.find_all('review'))

        return archive_info

    def __str__(self) -> str:
        return f'''
{self.info.article_title}
{self.info.authors}
{self.info.journal_title}, {self.info.copyright_year}
{self.info.doi}
{self.info.num_reviews} {"Review" if self.info.num_reviews == 1 else "Reviews"}
'''.strip()

    def __repr__(self) -> str:
        return self.__str__()