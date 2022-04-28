import requests
from typing import List, Optional, TypedDict, cast


class Author(TypedDict):
    corresp: Optional[str]
    orcid: Optional[str]
    position_idx: int
    given_names: Optional[str]
    surname: Optional[str]


class Review(TypedDict):
    source: str
    posting_date: str
    review_idx: str
    highlight: str
    related_article_doi: str
    text: str
    reviewed_by: str
    position_idx: int
    doi: str


class Annot(TypedDict):
    source: str
    posting_date: str
    review_idx: str
    highlight: str
    related_article_doi: str
    text: str
    reviewed_by: str
    position_idx: int
    doi: str


class ReviewProcess(TypedDict):
    reviews: List[Review]
    response: Optional[Review]
    annot: List[Annot]


class Article(TypedDict):
    id: int
    doi: str
    version: str
    source: str
    journal: str
    title: str
    abstract: str
    authors: List[Author]
    pub_date: str
    journal_doi: Optional[str]
    published_journal_title: Optional[str]
    nb_figures: int
    revdate: Optional[str]
    review_process: ReviewProcess
    entities: List[str]
    assays: List[str]
    main_topics: List[str]
    highlighted_entities: List[str]


def get_articles(doi: str) -> List[Article]:
    return cast(List[Article], requests.get(f'https://eeb.embo.org/api/v1/doi/{doi}').json())
