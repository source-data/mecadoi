from time import strptime, time_ns
from string import Template

from lxml import etree

from src.meca import MECArchive
from . import get_free_doi

DEPOSITION_TEMPLATE = Template("""<doi_batch
    xmlns="http://www.crossref.org/schema/5.3.1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    version="5.3.1"
    xsi:schemaLocation="http://www.crossref.org/schema/5.3.1 http://www.crossref.org/schemas/crossref5.3.1.xsd"
>
    <head>
        <doi_batch_id>${doi_batch_id}</doi_batch_id>
        <timestamp>${timestamp}</timestamp>
        <depositor>
            <depositor_name>${depositor_name}</depositor_name>
            <email_address>${depositor_email}</email_address>
        </depositor>
        <registrant>${registrant}</registrant>
    </head>
    <body></body>
</doi_batch>
""")

PEER_REVIEW_TEMPLATE = Template("""
<peer_review revision-round="${revision_round}" type="referee-report">
    <contributors>
        <anonymous sequence="first" contributor_role="author" />
    </contributors>
    <titles>
        <title>Review of ${article_title}</title>
    </titles>
    <review_date>
        <month>${review_date_month}</month>
        <day>${review_date_day}</day>
        <year>${review_date_year}</year>
    </review_date>
    <institution>
        <institution_name>${institution_name}</institution_name>
    </institution>
    <running_number>${running_number}</running_number>
    <rel:program xmlns:rel="http://www.crossref.org/relations.xsd">
        <rel:related_item>
            <rel:inter_work_relation relationship-type="isReviewOf" identifier-type="doi">${article_doi}</rel:inter_work_relation>
        </rel:related_item>
    </rel:program>
    <doi_data>
        <doi>${review_doi}</doi>
        <resource>${review_resource}</resource>
    </doi_data>
</peer_review>
""")

def generate_peer_review_deposition(meca: MECArchive, doi_db_file: str) -> bytes:
    """
    Generate a CrossRef deposition file for the peer reviews in the given MECA archive.

    If the archive does not contain any peer reviews, a ValueError is thrown.
    """
    if not meca.is_present(MECArchive.REVIEWS):
        raise ValueError('no reviews found in the given MECA archive')
    if not meca.article_preprint_doi:
        raise ValueError('no preprint DOI found in the given MECA archive')

    timestamp = time_ns()
    deposition_xml = etree.fromstring(
        DEPOSITION_TEMPLATE.substitute(
            doi_batch_id=f'rc.{timestamp}',
            timestamp=timestamp,
            depositor_name='EMBO',
            depositor_email='eidens@embl.de',
            registrant='EMBO',
        ),
        parser=etree.XMLParser(remove_blank_text=True),
    )

    body = deposition_xml[1]
    for review_xml in generate_reviews(meca, doi_db_file):
        body.append(review_xml)

    return etree.tostring(deposition_xml, pretty_print=True)

def generate_reviews(meca: MECArchive, doi_db_file: str):
    def assigned_date(meca_review):
        date = meca.get_el_with_attr(meca_review.history.date, 'date_type', 'assigned')
        return strptime(f'{date.year} {date.month} {date.day}', '%Y %m %d')

    doi_prefix = '10.15252'
    article_doi = meca.article_preprint_doi
    for revision_round in meca.reviews.version:
        revision = revision_round.revision
        for running_number, meca_review in enumerate(sorted(revision_round.review, key=assigned_date), start=1):
            review_date = meca.get_el_with_attr(meca_review.history.date, 'date_type', 'completed')
            review_resource = f'https://eeb.embo.org/doi/{article_doi}#rev{revision}-rr{running_number}'
            review_doi = get_free_doi(review_resource, doi_db_file=doi_db_file)
            yield etree.fromstring(
                PEER_REVIEW_TEMPLATE.substitute(
                    revision_round=revision,
                    article_title=meca.article_title,
                    review_date_year=review_date.year,
                    review_date_month=f'{review_date.month:02}',
                    review_date_day=f'{review_date.day:02}',
                    institution_name='Review Commons',
                    running_number=running_number,
                    article_doi=article_doi,
                    review_doi=review_doi,
                    review_resource=review_resource,
                ),
                parser=etree.XMLParser(remove_blank_text=True),
            )