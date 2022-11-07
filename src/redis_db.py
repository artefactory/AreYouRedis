import src.config as config
import asyncio
import numpy as np
import pandas as pd

# Set new event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from dateutil import parser
from typing import List, Dict
from src.vectors import create_embedding
from redis.asyncio import Redis
from redis.commands.search.query import Query
from redis.commands.search.field import VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from src.models import Paper


async def gather_with_concurrency(n, redis_conn, *papers):
    """
    Gathers all arXiv papers, and loads them in the redis DB, using the HSET function.
    
    The function was taken from the redis-arXiv repository; it still loads the abstract's embeddding ("vector"), 
    along with other variables, into the DB.
    
    > Several variables, coming from the raw data, were added to the mapping dictionary. 
        - submitter: Original author of the article (1 person)
        - authors: Authors, contributors (≥ 1 person)
        - doi: digital object identifiers, unique ids assigned to each arXiv article
        - version: Information regarding the article's different versions (was it replaced? when?)
        - license: Aticle's license
        - update_date: Date of last article's update
        - title: title
        - abstract: text of the abstract
        - categories: paper categories the article belongs to
        - month: Month of the last update
        - year: Year of the last update
        - sch_id: External data; Semantic Scholar's ID corresponding to the article's doi
        - citations: External data from Semantic Scholar; sch_id of all articles cited in this article.
        - influential_citation_count: Number of 'important' articles cited in this article / paper

    """
    semaphore = asyncio.Semaphore(n)

    async def load_paper(paper):
        async with semaphore:
            vector = paper.pop('vector')
            p = Paper(**paper)
            key = "paper_vector:" + str(p.id)
            # async write data to redis
            await p.save()
            await redis_conn.hset(
                key,
                mapping={
                    "paper_pk": p.pk,
                    "paper_id": p.id,
                    "submitter": p.submitter,
                    "authors": p.authors,
                    "doi": p.doi,
                    "version": p.versions,
                    "license": p.license,
                    "update_date": p.update_date,
                    "title": p.title,
                    "abstract": p.abstract,
                    "categories": p.categories,
                    "month": parser.parse(p.update_date).month,
                    "year": parser.parse(p.update_date).year,
                    "vector": np.array(vector, dtype=np.float32).tobytes(),
                    "sch_id": p.sch_id,
                    "citations": p.citations,
                    "influential_citation_count": p.influential_citation_count
                })

    # gather with concurrency
    await asyncio.gather(*[load_paper(p) for p in papers])


async def load_all_data(redis_conn: Redis, papers: pd.DataFrame):
    """
    Loads all the data inside the redis DB, and creates a vector index, to query the vectors efficiently.

    The function was taken from the redis-arXiv repository; 
    """
    if await redis_conn.dbsize() > 300:
        print("papers already loaded")
    else:
        print("Loading papers into Vecsim App")
        papers = papers.to_dict('records')
        await gather_with_concurrency(100, redis_conn, *papers)
        print("papers loaded!")

        print("Creating vector search index")
        # create a search index
        if config.INDEX_TYPE == "HNSW":
            await create_hnsw_index(redis_conn, len(papers), prefix="paper_vector:", distance_metric="IP")
        else:
            await create_flat_index(redis_conn, len(papers), prefix="paper_vector:", distance_metric="L2")
        print("Search index created")


def make_tag_fields():
    """Tag fields added during the index creation"""
    return [
        TagField('submitter'),
        TagField('authors'),
        TagField('doi'),
        TagField('categories'),
        TagField('year'),
        TagField('versions'),
        TagField('license'),
        TagField('update_date'),
    ]


def get_redis_connexion():
    """Redis connection pool, used to connect to the redis DB"""
    redis_connexion = Redis(
        host=config.REDIS_PUBLIC_URL,
        port=config.REDIS_PORT,
        password=config.REDIS_PASSWORD
    )
    return redis_connexion


async def create_index(
        redis_conn: Redis,
        prefix: str,
        vector_field: VectorField
):
    fields = make_tag_fields() + [vector_field]
    await redis_conn.ft(config.INDEX_NAME).create_index(
        fields=fields,
        definition=IndexDefinition(prefix=[prefix], index_type=IndexType.HASH)
    )


async def remove_index(
        redis_conn: Redis,
        index_name: str
):
    await redis_conn.ft(index_name).dropindex()


async def create_flat_index(
    redis_conn: Redis,
    number_of_vectors: int,
    prefix: str,
    distance_metric: str = 'L2'
):
    vector_field = VectorField(
        config.VECTOR_NAME,
        "FLAT", {
            "TYPE": config.VECTOR_TYPE,
            "DIM": config.VECTOR_DIM,
            "DISTANCE_METRIC": distance_metric,
            "INITIAL_CAP": number_of_vectors,
            "BLOCK_SIZE": number_of_vectors
        }
    )
    await create_index(redis_conn, prefix, vector_field)


async def create_hnsw_index(
    redis_conn: Redis,
    number_of_vectors: int,
    prefix: str,
    distance_metric: str = 'COSINE'
):
    vector_field = VectorField(
        config.VECTOR_NAME,
        "HNSW", {
            "TYPE": config.VECTOR_TYPE,
            "DIM": config.VECTOR_DIM,
            "DISTANCE_METRIC": distance_metric,
            "INITIAL_CAP": number_of_vectors,
        }
    )
    await create_index(redis_conn, prefix, vector_field)


def upload_vectors_to_redis(path: str = "./arxiv_embeddings_300000_completed.json"):
    papers_df = pd.read_json(path)
    conn = get_redis_connexion()
    for col in papers_df.columns:
        if col != "vector":
            papers_df[col] = papers_df[col].astype(str)

    asyncio.run(
        load_all_data(conn, papers_df)
    )


def format_tags(tag_dict: Dict[str, List[str]]):
    """Formats tags to query tag fields"""
    tags = ""
    for tag_name, tag_list in tag_dict.items():
        if tag_name in ['submitter', 'authors', 'doi', 'categories',
                        'year', 'versions', 'license', 'update_date'
                        ]:
            tag_list = " | ".join(tag_list)
            tags += f"@{tag_name}:{{{tag_list}}}"
    return f"({tags})"


def create_query(
    tag_dict: Dict[str, List[str]] = None,
    search_type: str = "KNN",
    number_of_results: int = 15,
) -> Query:
    tags = format_tags(tag_dict) if tag_dict else "*"
    base_query = f'{tags}=>[{search_type} {number_of_results} @vector $vec_param AS vector_score]'
    return Query(base_query)\
        .sort_by("vector_score")\
        .paging(0, number_of_results)\
        .return_fields("id", "paper_pk", "vector_score")\
        .dialect(2)


async def find_similar_papers_given_user_text(
        redis_conn: Redis,
        user_text: str,
        query: Query
):
    """
    Queries the DB using a similarity search, retrieves and processes the results.
    """
    # Execute query
    # noinspection PyUnresolvedReferences
    results = await redis_conn.ft(config.INDEX_NAME).search(
        query,
        query_params={
            "vec_param": create_embedding(user_text).tobytes()
        }
    )

    results = results.docs
    clean_score = [1 - float(doc.vector_score) for doc in results]
    processed_results = [await redis_conn.hgetall(doc.id) for doc in results]
    processed_results = [
        {try_decode_bytes(key): try_decode_bytes(value) for key, value in obj.items()}
        for obj in processed_results
    ]
    for p, score in zip(processed_results, clean_score):
        p.update({"similarity_score": score})

    return processed_results


def try_decode_bytes(data: bytes):
    """Converts bytes result from the query result into strings"""
    try:
        decoded = data.decode()
    except UnicodeDecodeError:
        decoded = data
    return decoded


def execute_user_query(
        user_text: str,
        k: int,
        year_min: int,
        year_max: int,
        categories: List[str] = None
):
    """Complete process: connects to the redis db, creates & runs the query."""

    r_conn = get_redis_connexion()
    filters_dict = {
        'year': [str(year) for year in range(year_min, year_max + 1, 1)]
    }
    if categories and len(categories) > 0:
        filters_dict['categories'] = categories

    q = create_query(
        tag_dict=filters_dict,
        number_of_results=k
    )
    result = asyncio.run(find_similar_papers_given_user_text(
        redis_conn=r_conn,
        user_text=user_text,
        query=q
    ))
    return result


def execute_user_query_example():
    r_conn = get_redis_connexion()
    q = create_query(number_of_results=1)
    result = asyncio.run(find_similar_papers_given_user_text(
        redis_conn=r_conn,
        user_text="machine learning model observability",
        query=q
    ))
    print(result)
