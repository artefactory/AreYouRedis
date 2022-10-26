import config
import asyncio
import redis
from redis.asyncio import Redis
from redis.commands.search.field import VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType


def make_tag_fields():
    # missing fields : title, comments, abstract (should be the vector), authors_parsed
    return [
        TagField('id'),
        TagField('submitter'),
        TagField('authors'),
        TagField('journal-ref'),
        TagField('doi'),
        TagField('report-no'),
        TagField('categories'),
        TagField('license'),
        TagField('versions'),
        TagField('update_date')
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


if __name__ == "__main__":

    conn = get_redis_connexion()
    # asyncio.run(
    #     create_flat_index(
    #         conn,
    #         1000,
    #         "test_flat_index:",
    #     )
    # )

    # asyncio.run(
    #     create_hnsw_index(
    #         conn,
    #         1000,
    #         "test_hnsw_index:",
    #     )
    # )

    asyncio.run(
        remove_index(conn, config.INDEX_NAME)
    )
