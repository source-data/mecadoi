import lxml.etree
from typing import Tuple
from xsdata.formats.dataclass.parsers import XmlParser
from zipfile import ZipFile

from .xml import (
    Article,
    Manifest,
    ReviewGroup,
    Transfer,
)

class MECArchive:
    """
    Read metadata from a MECA archive.

    To get started, pass a ZipFile to the constructor of this class: `meca = MECArchive(zip_file)`. This reads all
    metadata from the archive's XML files into the new  instance's `article`, `manifest`, `transfer`, and `reviews`
    attributes. For the structure of these objects, see their respective file in the `.xml` module.
    A few commonly accessed attributes are also set on the new instance: the title, DOI, copyright year, and journal of
    the article within the archive.
    """

    class MECAdata:
        """Describes a metadata file within a MECA archive."""
        def __init__(self, filename, data_class, validation_schema=None) -> None:
            self.filename = filename
            self.data_class = data_class
            self.validation_schema = validation_schema

    ARTICLE = MECAdata('article.xml', Article)
    MANIFEST = MECAdata('manifest.xml', Manifest, validation_schema='schemas/meca/manifest.dtd')
    REVIEWS = MECAdata('reviews.xml', ReviewGroup, validation_schema='schemas/meca/reviews.dtd')
    TRANSFER = MECAdata('transfer.xml', Transfer, validation_schema='schemas/meca/transfer.dtd')

    REQUIRED_FILES = [ARTICLE, MANIFEST, TRANSFER]
    METADATA_FILES = REQUIRED_FILES + [REVIEWS]

    def __init__(self, archive: ZipFile, strict_validation=False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._archive = archive
        self._files_in_archive = self._archive.namelist()

        is_valid, reason = self.is_valid(strict=strict_validation)
        if not is_valid:
            raise ValueError(f'not a valid MECA archive: {reason}')

        def parse(meca_data):
            if not self.is_present(meca_data):
                return None
            parser = XmlParser()
            with self._archive.open(meca_data.filename) as xml_file:
                return parser.parse(xml_file, clazz=meca_data.data_class)

        self.article = parse(MECArchive.ARTICLE)
        self.manifest = parse(MECArchive.MANIFEST)
        self.transfer = parse(MECArchive.TRANSFER)
        self.reviews = parse(MECArchive.REVIEWS)

        self.article_title = self.article.front.article_meta.title_group.article_title
        self.journal_title = self.article.front.journal_meta.journal_title_group.journal_title
        self.copyright_year = self.article.front.article_meta.permissions.copyright_year
        self.article_doi = self.get_el_with_attr(self.article.front.article_meta.article_id, 'pub_id_type', 'doi').value

    def is_valid(self, strict=False) -> Tuple[bool, str]:
        """
        Is this MECA archive valid?

        Checks if the given archive file is a valid ZIP file and that all required metadata files are present. If
        `strict=True` is passed, all metadata files (excluding article.xml) are validated against their schema
        definitions.
        """
        # check that the ZIP archive is valid
        first_bad_file = self._archive.testzip()
        if first_bad_file:
            return False, f'ZIP archive is invalid, first bad file: {first_bad_file}'

        # check that the MECA archive has all required files
        missing_required_files = []
        for required_file in MECArchive.REQUIRED_FILES:
            if not self.is_present(required_file):
                missing_required_files.append(required_file.filename)
        if missing_required_files:
            return False, f'MECA archive is missing these required files: {", ".join(missing_required_files)}'

        if strict:
            # validate the MECA files according to their schema
            invalid_files = []
            for meca_data in MECArchive.METADATA_FILES:
                schema_file = meca_data.validation_schema
                if not schema_file:
                    continue

                if schema_file.endswith('.xsd'):
                    xml_schema = lxml.etree.XMLSchema(
                        lxml.etree.parse(schema_file)
                    )
                elif schema_file.endswith('.dtd'):
                    xml_schema = lxml.etree.DTD(schema_file)
                else:
                    raise ValueError(f'no lxml validator class found for schema file {schema_file}')

                with self._open_file_in_archive(meca_data) as xml_file:
                    xml_doc = lxml.etree.parse(xml_file)
                    try:
                        xml_schema.assertValid(xml_doc)
                    except lxml.etree.DocumentInvalid as e:
                        invalid_files.append((meca_data.filename, e))
            if invalid_files:
                output = ''
                for invalid_filename, assertion_error in invalid_files:
                    output += f'''{invalid_filename}: {assertion_error.args}
'''
                return False, output

        return True, ''

    def is_present(self, meca_data: MECAdata) -> bool:
        """Is the given metadata file present in this MECA archive?"""
        return meca_data.filename in self._files_in_archive

    def get_el_with_attr(self, elements, attr: str, val: str):
        """
        Returns the first of the given elements that has the given attribute with the given value.
        
        Use it like so to get the element that holds the article's DOI:
        `meca.get_el_with_attr(meca.article.front.article_meta.article_id, 'pub_id_type', 'doi')`
        """
        el = [el for el in elements if getattr(el, attr) == val]
        return el[0] if el else None

    def __str__(self) -> str:
        return f'''
{self.article_title}
{self.article_doi}
{self.journal_title}, {self.copyright_year}
'''.strip()

    def __repr__(self) -> str:
        return self.__str__()