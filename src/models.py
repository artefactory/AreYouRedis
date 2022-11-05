from aredis_om import (
    Field,
    HashModel
)


class Paper(HashModel):
    id: str
    submitter: str
    authors: str
    doi: str
    categories: str
    year: str
    month: str
    versions: str
    license: str
    update_date: str
    title: str = Field(index=True, full_text_search=True)
    abstract: str = Field(index=True, full_text_search=True)
    sch_id: str
    citations: str
    influential_citation_count: str

