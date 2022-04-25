from requests import PreparedRequest, Request, Session
from src.config import CROSSREF_DEPOSITION_URL, CROSSREF_USERNAME, CROSSREF_PASSWORD


def pretty_print_request(req: PreparedRequest) -> None:
    print(req.method, req.url)
    for k, v in req.headers.items():
        print(f'{k}: {v}')

    body = req.body
    try:
        output = body.decode()  # type: ignore[union-attr] # since we catch the AttributeError when body is str or None
    except AttributeError:
        output = body

    print(output)


def prep_request(deposition_file: bytes, crossref_username: str, crossref_password: str) -> PreparedRequest:
    files = {'fname': ('deposition.xml', deposition_file)}
    data = {
        'login_id': crossref_username,
        'login_passwd': crossref_password,
    }
    url = CROSSREF_DEPOSITION_URL
    req = Request('POST', url, files=files, data=data)
    return req.prepare()


def deposit(deposition_file: bytes, verbose: int = 0) -> str:
    """Send a deposition file to the Crossref API."""
    if not (CROSSREF_USERNAME and CROSSREF_PASSWORD):
        raise ValueError('No CrossRef username or password given!')
    if verbose:
        pretty_print_request(prep_request(deposition_file, '***', '***'))

    req = prep_request(deposition_file, CROSSREF_USERNAME, CROSSREF_PASSWORD)
    resp = Session().send(req)
    resp.raise_for_status()
    return resp.text
