from datetime import datetime
from string import Template
from time import time_ns
from typing import Any, Callable, List, Union
from lxml import etree
from src.config import (
    DEPOSITOR_NAME,
    DEPOSITOR_EMAIL,
    REGISTRANT_NAME,
    INSTITUTION_NAME,
    REVIEW_RESOURCE_URL_TEMPLATE,
    REVIEW_TITLE_TEMPLATE,
    AUTHOR_REPLY_TITLE_TEMPLATE,
    AUTHOR_REPLY_RESOURCE_URL_TEMPLATE,
)
from src.model import Article, Author, AuthorReply


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


def generate_peer_review_deposition(
    article: Article,
    publication_date: datetime,
    doi_generator: Callable[[str], str],
) -> Any:
    """
    Generate a CrossRef deposition file for the peer reviews in the given article.

    If the article does not contain any peer reviews, a ValueError is thrown.
    """
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
    for review_xml in generate_reviews(article, publication_date, doi_generator):
        body.append(review_xml)

    return etree.tostring(deposition_xml, pretty_print=True)


def generate_reviews(
    article: Article,
    publication_date: datetime,
    doi_generator: Callable[[str], str],
) -> Any:
    if not article.preprint_doi:
        raise ValueError('no preprint DOI found in the given MECA archive')

    article_doi = article.preprint_doi
    article_title = article.title

    if not article.review_process:
        raise ValueError('no reviews found in the given MECA archive')
    for revision_round in article.review_process:
        revision = revision_round.revision_id
        review_dois = []
        for review in revision_round.reviews:
            title = Template(REVIEW_TITLE_TEMPLATE).substitute(article_title=article_title)
            resource_url = Template(REVIEW_RESOURCE_URL_TEMPLATE).substitute(
                article_doi=article_doi,
                revision=revision,
                running_number=review.running_number,
            )
            doi = doi_generator(resource_url)
            review_xml = template_xml(
                PEER_REVIEW_TEMPLATE,
                revision_round=revision,
                review_title=title,
                publication_date_year=publication_date.year,
                publication_date_month=f'{publication_date.month:02}',
                publication_date_day=f'{publication_date.day:02}',
                institution_name=INSTITUTION_NAME,
                running_number=review.running_number,
                article_doi=article_doi,
                review_doi=doi,
                review_resource=resource_url,
            )
            review_dois.append(doi)
            yield review_xml

        if revision_round.author_reply:
            title = Template(AUTHOR_REPLY_TITLE_TEMPLATE).substitute(article_title=article_title)
            resource_url = Template(AUTHOR_REPLY_RESOURCE_URL_TEMPLATE).substitute(
                article_doi=article_doi,
                revision=revision,
            )
            doi = doi_generator(resource_url)
            yield generate_author_reply(
                author_reply=revision_round.author_reply,
                title=title,
                doi=doi,
                resource_url=resource_url,
                article_doi=article_doi,
                revision=revision,
                review_dois=review_dois,
                publication_date=publication_date,
            )


PEER_REVIEW_TEMPLATE = Template("""
<peer_review revision-round="${revision_round}" type="referee-report">
    <contributors>
        <anonymous sequence="first" contributor_role="author" />
    </contributors>
    <titles>
        <title>${review_title}</title>
    </titles>
    <review_date>
        <month>${publication_date_month}</month>
        <day>${publication_date_day}</day>
        <year>${publication_date_year}</year>
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


AUTHOR_REPLY_TEMPLATE = Template("""
<peer_review revision-round="${revision_round}" type="author-comment">
    <contributors></contributors>
    <titles>
        <title>${author_reply_title}</title>
    </titles>
    <review_date>
        <month>${publication_date_month}</month>
        <day>${publication_date_day}</day>
        <year>${publication_date_year}</year>
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


def generate_author_reply(
    author_reply: AuthorReply,
    title: str,
    doi: str,
    resource_url: str,
    article_doi: str,
    revision: str,
    review_dois: List[str],
    publication_date: datetime,
) -> Any:
    author_reply_xml = template_xml(
        AUTHOR_REPLY_TEMPLATE,
        author_reply_title=title,
        revision_round=revision,
        publication_date_year=publication_date.year,
        publication_date_month=f'{publication_date.month:02}',
        publication_date_day=f'{publication_date.day:02}',
        institution_name=INSTITUTION_NAME,
        running_number="Author Reply",
        article_doi=article_doi,
        doi=doi,
        resource=resource_url,
    )

    for contributor in generate_contributors(author_reply.authors):
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


def generate_contributors(contributors: List[Author]) -> Any:
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
