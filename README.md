# AreYouRedis - Vector Search Engineering Hackathon 

This repository contains the code base built by the AreYouRedis team to create the "Darwinian Paper Explorer" app.

The hackathon - organised by the MLOps Community, in collaboration with Redis and Saturn Cloud - focused on Vector search engineering, on the arXiv dataset.

For more information on it, please visit the [hackathon's welcome page](https://hackathon.redisventures.com/)

## Submission summary

The submission is a streamlit app, hosted on **Saturn Cloud**, and accessible by [clicking on this link](https://pd-youss-areyouredi-ca51af7d090f4f20ab60bfc3d0e70e18.community.saturnenterprise.io/). 

The app's vision is to combine vector search and co-citations graph structures in order to:

- Help the user find arXiv articles linked to a subject he's interested in

- Provide the user with a view of a topic's trend, based on the number of related publications throughout time, along with a trend prediction for the next two years

- Illustrate how the subject of interest has evolved throughout history, with an arc diagram highlighting the founding / most influential papers and co-citation relationships between papers

- Recommend a curated reading list, based on a combination of vector similarity score and paper node degree in the citations graph


It takes as input a user's query - a sentence describing what type of arXiv papers a person is interested in searching - along with a set of filters on the year, categories, and number of similar papers to be retrieved.

Using **RedisSearch** capabilities, a set of similar articles, linked to the query, is obtained. 

Three output sections are then presented: 

1. Topic trend & future projection
2. Topic evolution
3. Reading list recommender - based on the papers' similarity scores and node degree in the citation graph
4. Papers overview




## Setting up the environment

First, clone the repository: 
```
git clone https://github.com/artefactory/AreYouRedis.git
```

Create a virtual environment at the root of your local repository:
```
python3 -m virtualenv .venv
source .venv/bin/activate
```

Install dependencies:
```
pip install -r requirements.txt
```

Finally, add the database's password as environment variable:
```
export REDIS_PASSWORD = '{password}'
```

## Running the app

To launch the app locally, run the following command:
```  
streamlit run app/app.py
```

The page below should open in your web browser:
![Darwinian paper searc](Darwinian_paper_explorer.png) 


### Repo structure
```
 .
├── LICENSE
├── Makefile
├── README.md
├── app
│   ├── app.py
│   ├── config_files
│   │   └── config.py
│   ├── features
│   │   └── topic_evolution.py
│   ├── main_page.py
│   ├── style
│   │   ├── Artefact_logo.png
│   │   ├── Artefact_small_logo.jpeg
│   │   ├── Redis_logo.png
│   │   ├── Saturncloud_logo.webp
│   │   └── style.css
│   └── utils
│       ├── display.py
│       ├── graph.py
│       ├── load_css.py
│       └── widgets.py
├── entrypoint.sh
├── notebooks
│   ├── custom-single-gpu-arxiv-embeddings.ipynb
│   ├── multi-gpu-arxiv-embeddings.ipynb
│   └── single-gpu-arxiv-embeddings.ipynb
├── requirements.in
├── requirements.txt
├── setup.py
└── src
    ├── categories.py
    ├── config.py
    ├── models.py
    ├── redis_db.py
    ├── scholar_citations.py
    └── vectors.py
```