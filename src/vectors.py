import json
import spacy
import pickle
import config
from tqdm import tqdm
from typing import Union, List
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


def clean_text(
        text: str,
        lowercase: bool = True,
        nlp=None
):
    if not nlp:
        nlp = spacy.load("en_core_web_sm")
    if lowercase:
        text = text.lower()
    text = nlp(text)

    # remove links, numbers and stopwords
    tokens = [token for token in text if (not token.is_stop) and token.text.isalpha()]
    lemmas = [token.lemma_ for token in tokens]
    text = " ".join(lemmas)
    return text


def vectorize(
        input_: Union[str, List[str]],
        write_to: str = None
):
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    vectors = model.encode(input_)

    if write_to:
        save_pickle(vectors, write_to)
    return vectors
