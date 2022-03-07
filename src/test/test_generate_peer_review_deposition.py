import lxml.etree
import zipfile

from src.meca import MECArchive
from src.crossref import generate_peer_review_deposition
from .common import DoiDbTestCase

class TestGeneratePeerReviewDeposition(DoiDbTestCase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.fixtures = [
            'mutagenesis',
            'signaling-pathway',
        ]
        self.maxDiff = None
        self.outputCanonicalFiles = False

    def test_generate_peer_review_deposition_for_empty_meca(self):
        with zipfile.ZipFile('src/test/test_data/no-reviews.zip', 'r') as archive:
            meca = MECArchive(archive)

        with self.assertRaises(ValueError):
            generate_peer_review_deposition(meca, 'src/test/tmp/out.xml', self.DOI_DB_FILE)

    def test_generate_peer_review_deposition(self):
        for meca_name in self.fixtures:
            with self.subTest(meca_name=meca_name):
                meca_archive = f'src/test/test_data/{meca_name}.zip'
                expected_xml = f'src/test/test_data/expected/{meca_name}.xml'
                actual_xml = self.generate_xml(meca_archive, meca_name)
                self.assertXmlEquals(meca_name, expected_xml, actual_xml)

    def generate_xml(self, meca_archive, meca_name):
        with zipfile.ZipFile(meca_archive, 'r') as archive:
            meca = MECArchive(archive)
            output_filename = f'src/test/tmp/{meca_name}.xml'
            generate_peer_review_deposition(meca, output_filename, self.DOI_DB_FILE)
            return output_filename

    def assertXmlEquals(self, meca_name, expected_xml_file, actual_xml_file):
        ignore_xpaths = [
            './cr:head/cr:doi_batch_id',
            './cr:head/cr:timestamp',
            './cr:body/cr:peer_review/cr:doi_data/cr:doi'
        ]
        ignore_namespaces = {'cr': 'http://www.crossref.org/schema/5.3.1'}

        def canonicalize(xml_file):
            tree = lxml.etree.parse(xml_file)
            root = tree.getroot()
            for ignore_xpath in ignore_xpaths:
                for element_to_ignore in root.findall(ignore_xpath, namespaces=ignore_namespaces):
                    parent = element_to_ignore.getparent()
                    parent.remove(element_to_ignore)

            return lxml.etree.canonicalize(
                xml_data=lxml.etree.tostring(root, encoding='unicode')
            )

        expected = canonicalize(expected_xml_file)
        actual = canonicalize(actual_xml_file)

        if self.outputCanonicalFiles is None:
            def write_xml(string, filename):
                with open(filename, 'w') as out:
                    out.write(string)
            write_xml(expected, f'src/test/tmp/{meca_name}.expected.xml')
            write_xml(actual, f'src/test/tmp/{meca_name}.actual.xml')

        self.assertEqual(expected, actual)

if __name__ == '__main__':
    unittest.main()
