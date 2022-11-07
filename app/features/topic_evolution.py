import streamlit as st
import asyncio
import calendar
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from matplotlib import pyplot as plt

from utils.widgets import update_session_state_var
from utils.graph import (
    get_graph_data,
    get_arc_graph
)
from utils.display import display_section_title
from src.redis_db import execute_user_query
from config_files import config
from statsmodels.tsa.holtwinters import Holt


def get_user_search_query():
    """
    Get user search query.
    """
    st.text_input(
        label="Enter topic of interest:",
        value=st.session_state.user_search_query,
        max_chars=100,
        key='user_search_query_text_input',
        on_change=update_session_state_var,
        kwargs={
            'session_state_var_name': 'user_search_query',
            'widget_key': 'user_search_query_text_input'
        }
    )


def get_search_filters():
    """
    Get search filters to be applied to the query.
    """
    col_1, col_2, col_3, col_4 = st.columns(4)
    with col_1:
        st.number_input(
            label="Select the number of similar papers",
            min_value=1,
            max_value=1000,
            value=st.session_state.k_similar,
            step=5,
            key='k_similar_number_input',
            on_change=update_session_state_var,
            kwargs={
                'session_state_var_name': 'k_similar',
                'widget_key': 'k_similar_number_input'
            }
        )

    with col_2:
        st.number_input(
            label="Select year lower bound",
            min_value=1990,
            max_value=st.session_state.year_max - 1,
            value=st.session_state.year_min,
            step=1,
            key='year_min_number_input',
            on_change=update_session_state_var,
            kwargs={
                'session_state_var_name': 'year_min',
                'widget_key': 'year_min_number_input'
            }
        )

    with col_3:
        st.number_input(
            label="Select year upper bound",
            min_value=st.session_state.year_min + 1,
            max_value=datetime.datetime.now().year,
            value=st.session_state.year_max,
            step=1,
            key='year_max_number_input',
            on_change=update_session_state_var,
            kwargs={
                'session_state_var_name': 'year_max',
                'widget_key': 'year_max_number_input'
            }
        )

    with col_4:
        st.multiselect(
            label='Select categories',
            options=list(config.arxiv_categories_mapping.keys()),
            default=st.session_state.categories,
            key='categories_multiselect',
            on_change=update_session_state_var,
            kwargs={
                'session_state_var_name': 'categories',
                'widget_key': 'categories_multiselect'
            }
        )


def update_sub_params():
    """
    Update 'sub' session state variables. Those variables are used to simulate a form behavior for the
    submit button, while allowing a dynamic behavior of the widgets inside the form.
    """
    st.session_state.user_search_query_sub = st.session_state.user_search_query
    st.session_state.categories_sub = st.session_state.categories
    st.session_state.year_min_sub = st.session_state.year_min
    st.session_state.year_max_sub = st.session_state.year_max
    st.session_state.k_similar_sub = st.session_state.k_similar


def set_submit_button():
    """
    Create a submit button widget to validate the query parameters.
    """
    st.button(
        label='Submit',
        type='primary',
        on_click=update_sub_params
    )


@st.experimental_memo
def get_search_query_results(user_search_query, k_similar, year_min, year_max, categories):
    """
    Get the search query results based on the user's query and search filters.

    Parameters
    ----------
    user_search_query : str
        User search query.
    k_similar : int
        Number of most similar papers to be retrieved.
    year_min : int
        Lower bound of the publication date for the papers to be retrieved
    year_max : int
        Upper bound of the publication date for the papers to be retrieved

    Returns
    ----------
    search_query_results : List(dict)
        List of search query results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    search_query_results = execute_user_query(
        user_text=user_search_query,
        k=k_similar,
        year_min=year_min,
        year_max=year_max,
        categories=[config.arxiv_categories_mapping[category] + "*" for category in categories]
    )
    # Add index based on position in result
    for i, paper in enumerate(search_query_results):
        paper['list_index'] = i

    return search_query_results


@st.experimental_memo
def display_topic_trend(query_results):
    """
    Display topic trend + optional prediction for the next two years if more than 5 non zero data points are available.

    Parameters
    ----------
    query_results : list(dict)
        List of most similar papers
    """
    dates = [int(el['year']) for el in query_results]
    weights = [1 for _ in query_results]
    all_dates = [year for year in range(min(dates), max(dates) + 1, 1)]
    zeros = [0] * len(all_dates)
    time_series_df = pd.DataFrame(
        {
            'date': dates + all_dates,
            'count_papers': weights + zeros
        }
    )
    time_series_df = time_series_df.groupby('date').sum().reset_index()

    fig = go.Figure(
        layout=go.Layout(
            xaxis=dict(
                title="Year"
            ),
            yaxis=dict(
                title="Papers count"
            ),
            margin=dict(t=30, b=30, l=1, r=1)
        )
    )
    fig.add_trace(
        go.Scatter(
            x=time_series_df['date'].values,
            y=time_series_df['count_papers'].values,
            name='Topic evolution',
            line=dict(color='#0097a7', width=4)
        )
    )

    # Predict topic trend for next 2 years if we have at least 5 year of history
    if len(all_dates) >= 5:
        ts_index = pd.date_range(start=str(min(dates)), end=str(max(dates) + 1), freq="A")
        ts_series = pd.Series(time_series_df['count_papers'].values, ts_index)
        pred = (
            Holt(ts_series, damped_trend=True, initialization_method="estimated")
            .fit(smoothing_level=0.8, smoothing_trend=0.2)
            .forecast(2)
        )
        fig.add_trace(
            go.Scatter(
                x=[year for year in range(max(dates), max(dates) + 3, 1)],
                y=np.concatenate([time_series_df['count_papers'].values[-1:], pred.values], axis=0),
                name='Predicted evolution',
                line=dict(color='#e71869 ', width=4, dash='dash')
            )
        )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


def display_arc_graph(query_results):
    """
    Display arc graph with citations relationships.

    Parameters
    ----------
    query_results : list(dict)
        List of most similar papers
    """
    col, _ = st.columns(2)
    col.info(
        "Please note that:  \n"
        "- Papers are ordered in chronological order.  \n"
        "- The size of a bubble is related to the number of citations of the paper.  \n"
        "- Links between bubbles represent citations."
    )
    graph_fig = get_arc_graph(get_graph_data(query_results))
    st.plotly_chart(
        figure_or_data=graph_fig,
        use_container_width=True
    )


@st.experimental_memo
def get_reading_list(query_results, K_reading_list):
    """
    Display arc graph with citations relationships.

    Parameters
    ----------
    query_results : list(dict)
        List of most similar papers
    """
    query_results = query_results.copy()
    for paper in query_results:
        paper['reading_score'] = len(paper['citations'].split(',')) * paper['similarity_score']
    # Select top K relevant
    reading_result = sorted(query_results, key=lambda d: d['reading_score'], reverse=True)[:K_reading_list]
    # Order by date
    reading_result = sorted(reading_result, key=lambda d: d['year'] + '-' + d['month'])
    return reading_result


def display_reading_list(query_results):
    """
    Display reading list with title, publication date, similarity score and number of citations.

    Parameters
    ----------
    query_results : list(dict)
        List of most similar papers
    """
    st.info(
        "The suggested reading list is based on the papers with the highest number of citations and similarity score. "
        "It is ordered by ascending publication date."
    )
    col_1, _, _ = st.columns(3)
    K_reading_list = col_1.number_input(
        label="Select the number of papers you're willing to read about this topic",
        min_value=1,
        max_value=st.session_state.k_similar,
        value=min(st.session_state.k_similar, 5),
        step=1
    )
    reading_result = get_reading_list(query_results, K_reading_list)

    ref_col, date_col, sim_col, citations_col = st.columns(4)
    with ref_col:
        display_section_title('Title (link)', 'tab_header')
    with date_col:
        display_section_title('Publication date', 'tab_header')
    with sim_col:
        display_section_title('Similarity score', 'tab_header')
    with citations_col:
        display_section_title('Citations', 'tab_header')

    max_citations = max([len(paper['citations'].split(',')) for paper in reading_result])
    for paper in reading_result:
        ref_col, date_col, sim_col, citations_col = st.columns(4)
        with ref_col:
            st.markdown(
                f'''<a target="_self" style='text-align: center; '''
                f'''font-size: 15px' href="#section-{paper['list_index']}">{paper['title']}</a>''',
                unsafe_allow_html=True
            )
        with date_col:
            date = f"{calendar.month_name[int(paper['month'])]} {paper['year']}"
            st.markdown(
                f"<h6 style='text-align: center; color: #010924; '>{date}</h6>",
                unsafe_allow_html=True
            )
        with sim_col:
            plt.rcParams["figure.autolayout"] = True
            plt.rcParams["figure.figsize"] = [7.50, 0.9]
            fig, ax = plt.subplots()
            ax.barh([''], [paper['similarity_score']], color="#49b6c2")
            ax.barh([''], [1 - paper['similarity_score']], left=[paper['similarity_score']], color="#939492")
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.get_xaxis().set_ticks([0, paper['similarity_score'], 1])
            ax.get_yaxis().set_ticks([])
            st.pyplot(fig)
        with citations_col:
            n_citations = len(paper['citations'].split(','))
            plt.rcParams["figure.autolayout"] = True
            plt.rcParams["figure.figsize"] = [7.50, 0.9]
            fig, ax = plt.subplots()
            ax.barh([''], [n_citations], color="#49b6c2")
            ax.barh([''], [max_citations - n_citations], left=[n_citations], color="#939492")
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.get_xaxis().set_ticks([0, n_citations, max_citations])
            ax.get_yaxis().set_ticks([])
            st.pyplot(fig)


def display_search_query_results(user_search_query_results):
    """
    Display a list of all results with detailed information about each paper. The list is ordered by descending similarity.

    Parameters
    ----------
    query_results : list(dict)
        List of most similar papers
    """
    st.markdown(
        """
        <style>
        .streamlit-expanderHeader {
            font-size: large;
            font-weight: bold;
        }
        </style>

        """,
        unsafe_allow_html=True,
    )
    for i in range(len(user_search_query_results)):
        res = user_search_query_results[i]
        st.markdown(
            f"""
            <a id="section-{res['list_index']}">\n</a>
            """,
            unsafe_allow_html=True
        )
        expander = st.expander(
            label=(
                f"{i + 1} - {res['title']}"
            )
        )
        with expander:
            st.markdown(
                (
                    f"**Author(s):** {res['authors']}  \n"
                    f"**Publication date:** {calendar.month_name[int(res['month'])]} {res['year']}  \n"
                    f"**Categories:** {res['categories']}  \n"
                    f"**Similarity score:** {round(res['similarity_score'], 2)}/1  \n"
                    f"**Number of citations:** {len(res['citations'].split(','))}  \n"
                    f"**Abstract:** {res['abstract']}  \n"
                    f"[Go to paper](https://arxiv.org/abs/{res['paper_id']})"
                )
            )
