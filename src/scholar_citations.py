import json
from tqdm import tqdm
import pandas as pd
from dateutil import parser
from semanticscholar import SemanticScholar
tqdm.pandas()


sch = SemanticScholar(api_key="")


# one scholar paper query
def get_sch_paper(ids: str, write_to: str = "./data/papers_citations/papers_meta.json"):

    paper = sch.get_paper(f'arXiv:{ids}')
    if paper:
        if paper.citations:
            citations = [
                {
                    'sch_id': p.paperId,
                    'arxiv_id': p.externalIds['ArXiv'] if (p.externalIds and 'ArXiv' in p.externalIds.keys()) else None,
                    'doi': p.externalIds['DOI'] if (p.externalIds and 'DOI' in p.externalIds.keys()) else None,
                    'influential_citation_count': p.influentialCitationCount
                } for p in paper.citations
            ]
        else:
            citations = None

        api_result = {
            'arxiv_id': ids,
            'sch_id': paper.paperId,
            'citations': citations,
            'doi': paper.externalIds['DOI'] if (paper.externalIds and 'DOI' in paper.externalIds.keys()) else None,
            'influential_citation_count': paper.influentialCitationCount
        }
        with open(write_to, "a") as f:
            json.dump(api_result, f)
            f.write("\n")


# do this after all api queries
def get_citations_df(from_: str, write_to: str = "./data/citations_dataframe.json"):
    data = []
    with open(from_, "r") as f:
        for jsonObj in f:
            dd = json.loads(jsonObj)
            data.append(dd)
    citations_dataframe = pd.DataFrame.from_records(data)
    citations_dataframe.to_json(write_to)
    return citations_dataframe


# do this after merge with embeddings
def fill_year_column(data: pd.DataFrame):
    """
    create year and month columns from Version 1 TAG
    """

    years = data.versions.progress_apply(lambda x: x[0]['created'])
    month = [parser.parse(x).month for x in years]
    years = [parser.parse(x).year for x in years]
    data['year'] = years
    data['month'] = month

    return data


# do this before uploading to redis
def process_citation(citation):

    """
    Get citation as str(list) of scholar ids
    """
    if citation:
        xx = [elem['sch_id'] for elem in citation]
        xx = [elem for elem in xx if isinstance(elem, str)]
        return ",".join(xx)
    else:
        return None
