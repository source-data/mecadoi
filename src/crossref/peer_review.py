""""""

__all__ = ["generate_peer_review_deposition"]

from string import Template
from time import time_ns
from typing import Generator, List
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
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
from src.article import Article
from src.crossref.xml.doi_batch import (
    Affiliations,
    Anonymous,
    Body,
    Contributors,
    Depositor,
    DoiBatch,
    DoiData,
    Head,
    Institution,
    InterWorkRelation,
    Orcid,
    PeerReview,
    PersonName,
    Program,
    RelatedItem,
    ReviewDate,
    Titles,
)
from src.model import Author


def generate_peer_review_deposition(article: Article) -> str:
    """Generate a CrossRef deposition file for the peer reviews in the given article.

    If the article does not contain any peer reviews, a ValueError is thrown.
    """
    num_reviews = (
        len(
            [
                r
                for revision_round in article.review_process
                for r in revision_round.reviews
            ]
        )
        if article.review_process
        else 0
    )
    if num_reviews == 0:
        raise ValueError("Article does not contain any reviews!")

    timestamp = time_ns()
    doi_batch = DoiBatch(
        version="5.3.1",
        schema_location="http://www.crossref.org/schema/5.3.1 http://www.crossref.org/schemas/crossref5.3.1.xsd",
        head=Head(
            doi_batch_id=f"rc.{timestamp}",
            timestamp=timestamp,
            depositor=Depositor(
                depositor_name=DEPOSITOR_NAME,
                email_address=DEPOSITOR_EMAIL,
            ),
            registrant=REGISTRANT_NAME,
        ),
        body=Body(
            peer_review=list(generate_reviews(article)),
        ),
    )

    serializer = XmlSerializer(
        config=SerializerConfig(pretty_print=True, xml_declaration=False)
    )
    namespaces = {
        "": "http://www.crossref.org/schema/5.3.1",
        "rel": "http://www.crossref.org/relations.xsd",
    }
    return serializer.render(doi_batch, ns_map=namespaces)


def generate_reviews(article: Article) -> Generator[PeerReview, None, None]:
    is_review_of_relation = RelatedItem(
        inter_work_relation=InterWorkRelation(
            relationship_type="isReviewOf",
            identifier_type="doi",
            value=article.doi,
        )
    )
    for revision, revision_round in enumerate(article.review_process):
        for running_number, review in enumerate(revision_round.reviews, start=1):
            title = Template(REVIEW_TITLE_TEMPLATE).substitute(
                article_title=article.title
            )
            resource_url = Template(REVIEW_RESOURCE_URL_TEMPLATE).substitute(
                article_doi=article.doi,
                revision=revision,
                running_number=running_number,
            )
            yield PeerReview(
                revision_round=revision,
                type="referee-report",
                stage="pre-publication",
                contributors=Contributors(
                    anonymous=Anonymous(sequence="first", contributor_role="author")
                ),
                titles=Titles(title=title),
                review_date=ReviewDate(
                    year=review.publication_date.year,
                    month=review.publication_date.month,
                    day=review.publication_date.day,
                ),
                institution=Institution(institution_name=INSTITUTION_NAME),
                running_number=str(running_number),
                program=Program(related_item=[is_review_of_relation]),
                doi_data=DoiData(
                    doi=review.doi,
                    resource=resource_url,
                ),
            )

        author_reply = revision_round.author_reply
        if author_reply:
            title = Template(AUTHOR_REPLY_TITLE_TEMPLATE).substitute(
                article_title=article.title
            )
            resource_url = Template(AUTHOR_REPLY_RESOURCE_URL_TEMPLATE).substitute(
                article_doi=article.doi,
                revision=revision,
            )
            yield PeerReview(
                revision_round=revision,
                type="author-comment",
                contributors=create_contributors(author_reply.authors),
                titles=Titles(title=title),
                review_date=ReviewDate(
                    year=author_reply.publication_date.year,
                    month=review.publication_date.month,
                    day=review.publication_date.day,
                ),
                institution=Institution(institution_name=INSTITUTION_NAME),
                running_number="Author Reply",
                program=Program(
                    related_item=[is_review_of_relation]
                    + [
                        RelatedItem(
                            inter_work_relation=InterWorkRelation(
                                relationship_type="isReplyTo",
                                identifier_type="doi",
                                value=review.doi,
                            )
                        )
                        for review in revision_round.reviews
                    ]
                ),
                doi_data=DoiData(
                    doi=author_reply.doi,
                    resource=resource_url,
                ),
            )


def create_contributors(authors: List[Author]) -> Contributors:
    contributors = Contributors(
        person_name=[
            PersonName(
                surname=author.surname,
                sequence="additional",
                contributor_role="author",
                given_name=author.given_name,
                affiliations=(
                    Affiliations(
                        institution=[
                            Institution(
                                institution_name=institution.name,
                                institution_department=institution.department,
                                institution_place=(
                                    f"{institution.city}, {institution.country}"
                                    if institution.city and institution.country
                                    else institution.city
                                    if institution.city
                                    else institution.country
                                    if institution.country
                                    else None
                                ),
                            )
                            for institution in author.institutions
                        ]
                    )
                    if author.institutions
                    else None
                ),
                orcid=(
                    Orcid(
                        authenticated=author.orcid.is_authenticated,
                        value=author.orcid.id,
                    )
                    if author.orcid
                    else None
                ),
            )
            for author in authors
        ]
    )

    # the contributor at the beginning of the contributors list gets to be first author
    if len(contributors.person_name) > 0:
        contributors.person_name[0].sequence = "first"

    return contributors
