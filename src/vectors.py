import re
import json
import pickle
import string
import pandas as pd
import config
import gcsfs
import sentence_transformers
from tqdm import tqdm
from sentence_transformers import SentenceTransformer


def save_pickle(obj, path: str) -> None:
    with open(path, 'wb') as f:
        pickle.dump(obj, f)


def load_pickle(path: str):
    with open(path, 'rb') as f:
        obj = pickle.load(f)
    return obj


def load_raw_data(path: str = "./data/arxiv-metadata-oai-snapshot.json"):
    arxiv_list = []
    with open(path) as f:
        for jsonObj in tqdm(f):
            arxiv = json.loads(jsonObj)
            arxiv_list.append(arxiv)
    return arxiv_list


def connect_gcloud(project: str = "data-sandbox-fr"):
    return gcsfs.GCSFileSystem(token=config.GCS_TOKEN_FILE, project=project)


def read_pickle_from_gcs(link: str):
    gcs_conn = connect_gcloud()
    with gcs_conn.open(link, 'rb') as file:
        content = pickle.load(file)
    return content


def read_pandas_json_from_gcs(link: str):
    return pd.read_json(link, storage_options={"token": config.GCS_TOKEN_FILE})


def add_missing_columns_to_embedding_file(
        embeddings_path: str = "./embeddings_100000.json",
        raw_data_path: str = "./arxiv-metadata-oai-snapshot.json",
        save_to: str = "./embeddings_100000_completed.json",
        sample_raw_data: int = 1500000

):
    embeddings = pd.read_json(embeddings_path)
    raw_data = load_raw_data(raw_data_path)
    raw_data = pd.DataFrame.from_records(raw_data)
    raw_data = raw_data.loc[:sample_raw_data]
    raw_data.id = raw_data.id.astype("float64")
    raw_data = raw_data[['id']+list(set(raw_data.columns) - set(embeddings.columns))]
    data = pd.merge(embeddings, raw_data, on="id", how="inner")
    data = data.fillna("None")
    data.to_json(save_to)
    print(f"File saved to {save_to}")


def clean_text(text: str):
    if not text:
        return ""
    # remove unicode characters
    text = text.encode('ascii', 'ignore').decode()
    # remove punctuation
    text = re.sub('[%s]' % re.escape(string.punctuation), ' ', text)
    # clean up the spacing
    text = re.sub('\s{2,}', " ", text)
    # remove urls
    text = re.sub("https*\S+", " ", text)
    # remove newlines
    text = text.replace("\n", " ")
    # remove all numbers
    text = re.sub('\w*\d+\w*', '', text)
    # split on capitalized words
    text = " ".join(re.split('(?=[A-Z])', text))
    # clean up the spacing again
    text = re.sub('\s{2,}', " ", text)
    return text.lower()


def create_embedding(
        text: str,
        model: sentence_transformers.SentenceTransformer = None
):
    if not model:
        model = SentenceTransformer(config.EMBEDDING_MODEL)
    embedding = model.encode(clean_text(text))
    return embedding
