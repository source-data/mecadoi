import os
import requests

CROSSREF_SANDBOX_URL='https://test.crossref.org/servlet/deposit'
CROSSREF_DEPOSITION_URL='https://example.org/servlet/deposit'

def pretty_print_request(req):
    print(req.method, req.url)
    for k, v in req.headers.items():
        print(f'{k}: {v}')
    print(req.body.decode())

def prep_request(deposition_file: bytes, crossref_username: str, crossref_password: str, sandbox: bool):
    files = {'fname': ('deposition.xml', deposition_file)}
    data = {
        'operation': 'doQueryUpload',
        'login_id': crossref_username,
        'login_passwd': crossref_password,
    }
    url = CROSSREF_SANDBOX_URL if sandbox else CROSSREF_DEPOSITION_URL
    req = requests.Request('POST', url, files=files, data=data)
    return req.prepare()

def deposit(deposition_file: bytes, crossref_username: str, crossref_password: str, verbose=False, sandbox=True) -> None:
    """Send a deposition file to the Crossref API."""
    if not (crossref_username and crossref_password):
        raise ValueError('No CrossRef username or password given!')
    if verbose:
        pretty_print_request(prep_request(deposition_file, '***', '***', sandbox))

    req = prep_request(deposition_file, crossref_username, crossref_password, sandbox)
    resp = requests.Session().send(req)
    resp.raise_for_status()
    return resp.text
