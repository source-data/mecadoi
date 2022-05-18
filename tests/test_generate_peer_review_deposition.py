from unittest import TestCase
import lxml.etree
from src.meca.archive import MECArchive
from src.crossref.peer_review import generate_peer_review_deposition


class TestGeneratePeerReviewDeposition(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.fixtures = [
            'mutagenesis',
            'signaling-pathway',
        ]
        self.invalid_fixtures = [
            'no-reviews',
            'no-preprint-doi',
        ]
        self.maxDiff = None
        self.outputCanonicalFiles = False

    def test_generate_peer_review_deposition_for_invalid_meca(self) -> None:
        for meca_name in self.invalid_fixtures:
            with self.subTest(meca_name=meca_name):
                meca = MECArchive(f'tests/test_data/{meca_name}.zip')

                with self.assertRaises(ValueError):
                    generate_peer_review_deposition(meca)

    def test_generate_peer_review_deposition(self) -> None:
        for meca_name in self.fixtures:
            with self.subTest(meca_name=meca_name):
                meca_archive = f'tests/test_data/{meca_name}.zip'
                expected_xml = f'tests/test_data/expected/{meca_name}.xml'
                actual_xml = self.generate_xml(meca_archive, meca_name)
                self.assertXmlEquals(meca_name, expected_xml, actual_xml)

    def generate_xml(self, meca_archive: str, meca_name: str) -> str:
        meca = MECArchive(meca_archive)
        output_filename = f'tests/tmp/{meca_name}.xml'
        deposition_xml = generate_peer_review_deposition(meca)
        with open(output_filename, 'wb') as f:
            f.write(deposition_xml)
        return output_filename

    def assertXmlEquals(self, meca_name: str, expected_xml_file: str, actual_xml_file: str) -> None:
        ignore_xpaths = [
            './cr:head/cr:doi_batch_id',
            './cr:head/cr:timestamp',
            './cr:body/cr:peer_review/cr:doi_data/cr:doi',
            './cr:body/cr:peer_review/rel:program/rel:related_item/rel:inter_work_relation',
            './cr:body/cr:peer_review[@type="author-comment"]/cr:review_date',
        ]
        ignore_namespaces = {
            'cr': 'http://www.crossref.org/schema/5.3.1',
            'rel': 'http://www.crossref.org/relations.xsd',
        }

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

        expected = canonicalize(expected_xml_file)
        actual = canonicalize(actual_xml_file)

        if self.outputCanonicalFiles is None:
            def write_xml(string: str, filename: str):
                with open(filename, 'w') as out:
                    out.write(string)
            write_xml(expected, f'tests/tmp/{meca_name}.expected.xml')
            write_xml(actual, f'tests/tmp/{meca_name}.actual.xml')

        self.assertEqual(expected, actual)
