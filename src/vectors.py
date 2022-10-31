import re
import json
import pickle
import string
import pandas as pd
import config
import itertools
import networkx as nx
import sentence_transformers
import matplotlib.pyplot as plt
from tqdm import tqdm
from categories import _map
from typing import List
from sentence_transformers import SentenceTransformer
tqdm.pandas()


def save_pickle(obj, path: str) -> None:
    with open(path, 'wb') as f:
        pickle.dump(obj, f)


def load_pickle(path: str):
    with open(path, 'rb') as f:
        obj = pickle.load(f)
    return obj


def load_raw_data(path: str = "./../lib/data/arxiv-metadata-oai-snapshot.json"):
    arxiv_list = []
    with open(path) as f:
        for jsonObj in tqdm(f):
            arxiv = json.loads(jsonObj)
            arxiv_list.append(arxiv)
    return arxiv_list


def map_categories_to_value(categories: pd.Series):
    mapping = {key.lower(): value.lower() for key, value in _map.items()}
    categories = categories.str.lower()
    return categories.replace(mapping)


def add_missing_columns_to_embedding_file(
        embeddings_path: str = "./arxiv_embeddings_300000.json",
        raw_data_path: str = "./arxiv-metadata-oai-snapshot.json",
        save_to: str = "./arxiv_embeddings_300000_completed.json",
        sample_raw_data: int = None

):
    embeddings = pd.read_json(embeddings_path)
    embeddings.categories = map_categories_to_value(embeddings.categories)

    raw_data = load_raw_data(raw_data_path)
    raw_data = pd.DataFrame.from_records(raw_data)
    if sample_raw_data:
        raw_data = raw_data.loc[:sample_raw_data]
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


def clean_authors_parsed(authors_parsed_list: List[List[str]]):
    res = []
    for sublist in authors_parsed_list:
        authors = " ".join(sublist).strip().lower()
        authors = re.sub(' +', ' ', authors)
        res.append(authors)
    return res


def capitalize(obj: any):
    try:
        obj = obj.title()
        return obj
    except AttributeError:
        return obj


def get_all_authors_edges(data_path: str = "./arxiv_embeddings_300000_completed.json"):

    """
    1 - Get paper authors name from authors_parsed_column
    2 - Compute all combinations (duos) of authors on the paper (each author has published with all others)
    3 - Count each duo occurrence as score - (to evolve)
    4 - return flattened duos + score list as weighted edge for nx
    """

    data = pd.read_json(data_path)
    authors_parsed = data.authors_parsed
    del data
    combinations = []

    for val in tqdm(authors_parsed):
        cleaned_val = clean_authors_parsed(val)
        if len(cleaned_val) > 1:
            combi = list(itertools.combinations(cleaned_val, 2))
            combinations += [combi]
        else:
            pass
    del authors_parsed
    combinations = [item for sublist in tqdm(combinations) for item in sublist]
    combinations = pd.Series(combinations).value_counts(ascending=False)
    combinations = combinations.to_frame().reset_index()
    combinations = combinations.rename(columns={0: "score", "index": "authors"})
    combinations = combinations[combinations["score"] > 1]
    combinations["tuple_score"] = combinations["score"].apply(lambda x: (x,))
    combinations["weighted_edges"] = combinations.authors + combinations.tuple_score
    return combinations["weighted_edges"]


def get_top_collab(weighted_edges: List, author: str, sample: int = 3):

    """
    Return : The top 3 biggest (top sample) collab for the actual author in terms of score
    This author has published x times with this other one as score
    """
    focus = [elem for elem in weighted_edges if author in elem]
    focus = sorted(focus, key=lambda x: x[2], reverse=True)
    return focus[:sample]


def get_authors_edges(
        weighted_edges: List,
        author: str,
        sample: int = 3,
        make_graph: bool = True
):

    """
    1 - get top 3 biggest collaborators of the actual author
    2 - for each of the collaborators, get the top 3 of their collaborators
    3 - add the duos + score as edge to a nx graph
    4 - make the graph
    """

    author = author.lower()
    top_collab = get_top_collab(weighted_edges, author, sample)
    collaborators = [item for sublist in top_collab
                     for item in sublist
                     if not isinstance(item, int)
                     and item != author]
    for coll in collaborators:
        top_collab += get_top_collab(weighted_edges, coll, sample)

    top_collab = [tuple([capitalize(x) for x in sub]) for sub in top_collab]
    if make_graph:
        g = nx.Graph()
        g.add_weighted_edges_from(top_collab)
        return top_collab, g

    return top_collab, None


def plot_graph(g, node: str):
    pos = nx.spring_layout(g, scale=10)
    nx.draw_networkx(g, pos=pos, font_size=16, node_color='white',
                     font_color='black', alpha=.5)
    nx.draw_networkx(g.subgraph(node), pos=pos, font_size=16,
                     node_color='white', font_color='green', alpha=.5)
    plt.show()

# if __name__ == "__main__":
#
#     # the following statement takes some time
#     all_edges = get_all_authors_edges()
#
#     author_name = "Ma W."
#     author_collabs, g = get_authors_edges(all_edges, author_name, 3)
#     plot_graph(g, node=author_name)
