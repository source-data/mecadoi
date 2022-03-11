import os
import requests

CROSSREF_DEPOSITION_URL='https://test.crossref.org/servlet/deposit'

def pretty_print_request(req):
    print(req.method, req.url)
    for k, v in req.headers.items():
        print(f'{k}: {v}')
    print(req.body.decode())

def prep_request(deposition_file: bytes, crossref_username: str, crossref_password: str):
    files = {'fname': ('deposition.xml', deposition_file)}
    data = {
        'operation': 'doQueryUpload',
        'login_id': crossref_username,
        'login_passwd': crossref_password,
    }
    req = requests.Request('POST', CROSSREF_DEPOSITION_URL, files=files, data=data)
    return req.prepare()

def deposit(deposition_file: bytes, crossref_username: str, crossref_password: str, verbose=False) -> None:
    """Send a deposition file to the Crossref API."""
    if verbose:
        pretty_print_request(prep_request(deposition_file, '***', '***'))

    req = prep_request(deposition_file, crossref_username, crossref_password)
    resp = requests.Session().send(req)
    resp.raise_for_status()
    return resp.text
