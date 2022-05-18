from datetime import datetime
from string import Template
from time import time_ns
from typing import Any, List, Union
from lxml import etree
from src.config import (
    DEPOSITOR_NAME,
    DEPOSITOR_EMAIL,
    REGISTRANT_NAME,
    INSTITUTION_NAME,
    REVIEW_RESOURCE_URL_TEMPLATE,
    AUTHOR_REPLY_RESOURCE_URL_TEMPLATE,
)
from src.dois import get_free_doi
from src.meca.archive import AuthorReplyInfo, AuthorInfo, MECArchive, ReviewInfo


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


def generate_peer_review_deposition(meca: MECArchive) -> Any:
    """
    Generate a CrossRef deposition file for the peer reviews in the given MECA archive.

    If the archive does not contain any peer reviews, a ValueError is thrown.
    """
    if not meca.reviews:
        raise ValueError('no reviews found in the given MECA archive')
    if not meca.article_preprint_doi:
        raise ValueError('no preprint DOI found in the given MECA archive')

    timestamp = time_ns()
    deposition_xml = etree.fromstring(
        DEPOSITION_TEMPLATE.substitute(
            doi_batch_id=f'rc.{timestamp}',
            timestamp=timestamp,
            depositor_name=DEPOSITOR_NAME,
            depositor_email=DEPOSITOR_EMAIL,
            registrant=REGISTRANT_NAME,
        ),
        parser=etree.XMLParser(remove_blank_text=True),
    )

    body = deposition_xml[1]
    for review_xml in generate_reviews(meca):
        body.append(review_xml)

    return etree.tostring(deposition_xml, pretty_print=True)


def generate_reviews(meca: MECArchive) -> Any:
    article_doi = meca.article_preprint_doi
    if not article_doi:
        raise ValueError()
    article_title = meca.article_title
    if not article_title:
        raise ValueError()
    revision = None
    for index, revision_round in enumerate(meca.revision_rounds):
        revision = revision_round.revision or index
        review_dois = []
        for review in revision_round.reviews:
            doi, review_xml = generate_review(article_doi, article_title, revision, review)
            review_dois.append(doi)
            yield review_xml

        if revision_round.author_reply:
            yield generate_author_reply(article_doi, article_title, revision, review_dois, revision_round.author_reply)


PEER_REVIEW_TEMPLATE = Template("""
<peer_review revision-round="${revision_round}" type="referee-report">
    <contributors>
        <anonymous sequence="first" contributor_role="author" />
    </contributors>
    <titles>
        <title>Peer Review of ${article_title}</title>
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
            <rel:inter_work_relation
                relationship-type="isReviewOf"
                identifier-type="doi"
            >${article_doi}</rel:inter_work_relation>
        </rel:related_item>
    </rel:program>
    <doi_data>
        <doi>${review_doi}</doi>
        <resource>${review_resource}</resource>
    </doi_data>
</peer_review>
""")


def generate_review(article_doi: str, article_title: str, revision: int, review: ReviewInfo) -> Any:
    running_number = review.running_number
    review_resource = Template(REVIEW_RESOURCE_URL_TEMPLATE).substitute(
        article_doi=article_doi,
        revision=revision,
        running_number=running_number,
    )
    review_doi = get_free_doi(review_resource)
    review_date = review.date_completed
    review_xml = template_xml(
        PEER_REVIEW_TEMPLATE,
        revision_round=revision,
        article_title=article_title,
        review_date_year=review_date.year,
        review_date_month=f'{review_date.month:02}',
        review_date_day=f'{review_date.day:02}',
        institution_name=INSTITUTION_NAME,
        running_number=running_number,
        article_doi=article_doi,
        review_doi=review_doi,
        review_resource=review_resource,
    )
    return review_doi, review_xml


AUTHOR_REPLY_TEMPLATE = Template("""
<peer_review revision-round="${revision_round}" type="author-comment">
    <contributors></contributors>
    <titles>
        <title>Author Reply to Peer Reviews of ${article_title}</title>
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
            <rel:inter_work_relation
                relationship-type="isReviewOf"
                identifier-type="doi"
            >${article_doi}</rel:inter_work_relation>
        </rel:related_item>
    </rel:program>
    <doi_data>
        <doi>${doi}</doi>
        <resource>${resource}</resource>
    </doi_data>
</peer_review>
""")
AUTHOR_REPLY_REVIEW_RELATION_TEMPLATE = Template("""
<rel:related_item xmlns:rel="http://www.crossref.org/relations.xsd">
    <rel:inter_work_relation
        relationship-type="isReplyTo"
        identifier-type="doi"
    >${review_doi}</rel:inter_work_relation>
</rel:related_item>
""")


def generate_author_reply(article_doi: str, article_title: str, revision: int, review_dois: List[str],
                          author_reply: AuthorReplyInfo) -> Any:
    author_reply_resource = Template(AUTHOR_REPLY_RESOURCE_URL_TEMPLATE).substitute(
        article_doi=article_doi,
        revision=revision,
    )
    author_reply_doi = get_free_doi(author_reply_resource)
    author_reply_date = datetime.now()
    author_reply_xml = template_xml(
        AUTHOR_REPLY_TEMPLATE,
        revision_round=revision,
        article_title=article_title,
        review_date_year=author_reply_date.year,
        review_date_month=f'{author_reply_date.month:02}',
        review_date_day=f'{author_reply_date.day:02}',
        institution_name=INSTITUTION_NAME,
        running_number="Author Reply",
        article_doi=article_doi,
        doi=author_reply_doi,
        resource=author_reply_resource,
    )

    for contributor in generate_contributors(author_reply.contributors):
        author_reply_xml[0].append(contributor)

    for review_doi in review_dois:
        relation_to_review = template_xml(AUTHOR_REPLY_REVIEW_RELATION_TEMPLATE, review_doi=review_doi)
        author_reply_xml[5].append(relation_to_review)

    return author_reply_xml


CONTRIBUTOR_TEMPLATE = Template("""
<person_name contributor_role="author" sequence="${sequence}">
    <given_name>${given_name}</given_name>
    <surname>${surname}</surname>
</person_name>
""")
AFFILIATION_TEMPLATE = Template("""
<affiliations>
    <institution>
        <institution_name>${institution_name}</institution_name>
    </institution>
</affiliations>
""")
ORCID_TEMPLATE = Template('<ORCID authenticated="${is_authenticated}">${orcid}</ORCID>')


def generate_contributors(contributors: List[AuthorInfo]) -> Any:
    sequence = 'first'
    for contributor in contributors:
        contributor_xml = template_xml(
            CONTRIBUTOR_TEMPLATE,
            sequence=sequence,
            given_name=contributor.given_name,
            surname=contributor.surname,
        )
        sequence = 'additional'  # the contributor at the beginning of the contributors list gets to be first author
        if contributor.affiliation:
            contributor_xml.append(
                template_xml(AFFILIATION_TEMPLATE, institution_name=contributor.affiliation)
            )
        if contributor.orcid:
            contributor_xml.append(
                template_xml(
                    ORCID_TEMPLATE,
                    orcid=contributor.orcid.id,
                    is_authenticated='true' if contributor.orcid.is_authenticated else 'false',
                )
            )
        yield contributor_xml


def template_xml(template: Template, **kwargs: Union[str, int]) -> Any:
    return etree.fromstring(
        template.substitute(**kwargs),
        parser=etree.XMLParser(remove_blank_text=True),
    )
