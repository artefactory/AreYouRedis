import os

REDIS_PUBLIC_URL = "redis-10525.c21908.eu-west1-2.gcp.cloud.rlrcp.com"
REDIS_PORT = 10525

INDEX_NAME = "papers"
INDEX_TYPE = "HNSW"

VECTOR_NAME = "vector"
VECTOR_TYPE = "FLOAT32"
VECTOR_DIM = 768
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

GCS_TOKEN_FILE = ""
GCS_PROJECT = ""
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")
REDIS_USERNAME = "default"
