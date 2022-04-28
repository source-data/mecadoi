import re
from typing import cast
import responses
from unittest import TestCase
from unittest.mock import Mock, patch
from src.config import CROSSREF_DEPOSITION_URL, CROSSREF_USERNAME, CROSSREF_PASSWORD
from src.crossref.api import deposit
from src.crossref.verify import VerificationResult


class TestDepositPeerReviews(TestCase):

    @responses.activate
    @patch(
        'src.crossref.api.verify',
        return_value=[
            VerificationResult(all_reviews_present=True, error=None, preprint_doi='doi')
        ],
    )
    def test_deposit_peer_reviews(self, _: Mock) -> None:
        """
        Test whether the correct request is sent to the Crossref API when depositing peer reviews.
        """
        # Set up responses, which mocks out the requests library we use
        expected_response = '<html><head><title>SUCCESS</title></head><body><h2>SUCCESS</h2></body></html>'
        responses.add(responses.POST, CROSSREF_DEPOSITION_URL, body=expected_response, status=200)

        deposition_xml = '<doi_batch><head></head><body></body></doi_batch>'
        actual_response = deposit(deposition_xml.encode())
        self.assertEqual(expected_response, actual_response)

        self.assertEqual(1, len(responses.calls))
        actual_request = responses.calls[0].request
        self.assertEqual(CROSSREF_DEPOSITION_URL, actual_request.url)

        self.assertIn('Content-Type', actual_request.headers)
        content_type = actual_request.headers['Content-Type']

        re_content_type = re.compile('^multipart/form-data; boundary=(.+)$')
        self.assertRegex(content_type, re_content_type)

        match = re_content_type.match(content_type)
        self.assertIsNotNone(match)
        multipart_boundary = match[1]  # type: ignore[index] # the previous line ensures it's not None

        expected_body = f"""--{multipart_boundary}
Content-Disposition: form-data; name="login_id"

{CROSSREF_USERNAME}
--{multipart_boundary}
Content-Disposition: form-data; name="login_passwd"

{CROSSREF_PASSWORD}
--{multipart_boundary}
Content-Disposition: form-data; name="fname"; filename="deposition.xml"

{deposition_xml}
--{multipart_boundary}--
"""
        actual_body = actual_request.body
        if actual_body:
            try:
                actual_body = actual_body.decode()  # type: ignore[union-attr] # we catch the AttrError when it's a str
            except AttributeError:
                pass
            actual_body = cast(str, actual_body)
            actual_body = actual_body.replace('\r', '')
        self.maxDiff = None
        self.assertEqual(expected_body, actual_body)
