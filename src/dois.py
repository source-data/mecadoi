"""Handles the creation of random DOIs and tries to ensure they are not reused."""

__all__ = ["get_random_doi", "get_free_doi"]

from datetime import datetime
from secrets import choice
from sqlalchemy.exc import IntegrityError
from string import digits, Template

from src.config import DOI_TEMPLATE
from src.db import BatchDatabase


def get_free_doi(doi_db: BatchDatabase, resource: str) -> str:
    """
    Get an unused DOI for the given resource.

    The DOIs are created according to the template defined in the DOI_TEMPLATE configuration parameter. The template
    must contain two $-substitution parameters called "year" and "random" which will be replaced with the current year
    and a string of 6 random digits, respectively. For example, the template "10.15252/rc.$year$random" produces DOIs
    like "10.15252/rc.2022123456".

    The DOI that this function returns is stored, with the given resource and a timestamp, in the DOI database. It's
    an sqlite3 database located at the path set in the DOI_DB_FILE configuration parameter.

    IMPORTANT: wether a DOI is unused depends solely on wether it has already been marked as used in the currently
    configured DOI database. Therefore, if the database or its contents are modified, or a different database is
    configured, a previously used DOI may be returned by this function.

    The function will try multiple times to create a random, unused DOI. If it still fails to create an unused DOI
    after these attempt, an Exception is raised.
    """
    doi = None
    max_num_tries = 10
    num_tries = 0
    while doi is None and num_tries < max_num_tries:
        num_tries += 1
        doi = get_random_doi()
        try:
            doi_db.mark_doi_as_used(doi, resource)
        except IntegrityError:
            # this means the DOI has already been used
            doi = None
    if doi is None:
        raise Exception(f"failed to generate unused DOI in {max_num_tries} tries")

    return doi


def get_random_doi() -> str:
    # create the random part of the DOI: a string of 6 random digits
    population = digits
    k = 6
    random_part = "".join([choice(population) for i in range(k)])
    year = str(datetime.now().year)
    return Template(DOI_TEMPLATE).substitute(year=year, random=random_part)
