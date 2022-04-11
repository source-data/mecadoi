import re
import responses
import unittest
from src.crossref import deposit
from src.crossref.api import CROSSREF_SANDBOX_URL

class TestDepositPeerReviews(unittest.TestCase):

    @responses.activate
    def test_deposit_peer_reviews(self):
        """
        Test whether the correct request is sent to the Crossref API when depositing peer reviews.
        """
        # Set up responses, which mocks out the requests library we use
        expected_response = '<html><head><title>SUCCESS</title></head><body><h2>SUCCESS</h2><p>Your batch submission was successfully received.</p></body></html>'
        responses.add(responses.POST, CROSSREF_SANDBOX_URL, body=expected_response, status=200)

        deposition_xml = '<doi_batch><head></head><body></body></doi_batch>'
        crossref_username = 'crossref_username'
        crossref_password = 'crossref_password'
        actual_response = deposit(deposition_xml, crossref_username, crossref_password, sandbox=True)
        self.assertEqual(expected_response, actual_response)

        self.assertEqual(1, len(responses.calls))
        actual_request = responses.calls[0].request
        self.assertEqual(CROSSREF_SANDBOX_URL, actual_request.url)

        self.assertIn('Content-Type', actual_request.headers)
        content_type = actual_request.headers['Content-Type']

        re_content_type = re.compile('^multipart/form-data; boundary=(.+)$')
        self.assertRegex(content_type, re_content_type)

        multipart_boundary = re_content_type.match(content_type)[1]
        expected_body = f"""--{multipart_boundary}
Content-Disposition: form-data; name="operation"

doQueryUpload
--{multipart_boundary}
Content-Disposition: form-data; name="login_id"

{crossref_username}
--{multipart_boundary}
Content-Disposition: form-data; name="login_passwd"

{crossref_password}
--{multipart_boundary}
Content-Disposition: form-data; name="fname"; filename="deposition.xml"

{deposition_xml}
--{multipart_boundary}--
"""

        actual_body = actual_request.body.replace(b'\r', b'').decode()
        self.maxDiff = None
        self.assertEqual(expected_body, actual_body)

if __name__ == '__main__':
    unittest.main()
