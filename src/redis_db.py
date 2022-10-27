import config
import asyncio
import numpy as np
import pandas as pd
from dateutil import parser
from typing import List, Dict
from vectors import create_embedding
from redis.asyncio import Redis
from redis.commands.search.query import Query
from redis.commands.search.field import VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
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
    versions: str
    license: str
    update_date: str
    title: str = Field(index=True, full_text_search=True)
    abstract: str = Field(index=True, full_text_search=True)


async def gather_with_concurrency(n, redis_conn, *papers):
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
                })

    # gather with concurrency
    await asyncio.gather(*[load_paper(p) for p in papers])


async def load_all_data(redis_conn: Redis, papers: pd.DataFrame):
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


def upload_vectors_to_redis(path: str = "./embeddings_100000_completed.json"):
    papers_df = pd.read_json(path)
    conn = get_redis_connexion()
    for col in papers_df.columns:
        if col != "vector":
            papers_df[col] = papers_df[col].astype(str)

    asyncio.run(
        load_all_data(conn, papers_df)
    )


def format_tags(tag_dict: Dict[str, List[str]]):
    tags = ""
    for tag_name, tag_list in tag_dict.items():
        if tag_name in ['submitter', 'authors', 'doi', 'categories',
                        'year', 'versions', 'license', 'update_date'
                        ]:
            tag_list = " | ".join(tag_list)
            tags += f"@{tag_name}:{{{tag_list}}}"
    return f"({tags})"


def create_query(
    tag_dict:  Dict[str, List[str]] = None,
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


async def process_paper(p):
    paper = await Paper.get(p.paper_pk)
    paper = paper.dict()
    paper['similarity_score'] = 1 - float(p.vector_score)
    return paper


async def papers_from_results(results) -> list:
    return [await process_paper(p) for p in results.docs]


async def find_similar_papers_given_id(
        redis_conn: Redis,
        paper_id: str,
        query: Query
):
    # find the vector of the Paper listed in the request
    paper_vector_key = "paper_vector:" + paper_id
    vector = await redis_conn.hget(paper_vector_key, "vector")
    # Execute query
    # noinspection PyUnresolvedReferences
    results = await redis_conn.ft(config.INDEX_NAME).search(
        query,
        query_params={"vec_param": vector}
    )
    return await papers_from_results(results)


async def find_similar_papers_given_user_text(
        redis_conn: Redis,
        user_text: str,
        query: Query
):
    # Execute query
    # noinspection PyUnresolvedReferences
    results = await redis_conn.ft(config.INDEX_NAME).search(
        query,
        query_params={
            "vec_param": create_embedding(user_text).tobytes()
        }
    )
    return await papers_from_results(results)


# if __name__ == "__main__":
#
#     r_conn = get_redis_connexion()
#     # q = create_query()
#     q = create_query(tag_dict={"year": ["2007", "2008", "2009", "2010"]})
#
#     # res = asyncio.run(find_similar_papers_given_id(r_conn, "711.187", q))
#     res = asyncio.run(find_similar_papers_given_user_text(
#         redis_conn=r_conn,
#         user_text="An article about computer science",
#         query=q
#     ))
