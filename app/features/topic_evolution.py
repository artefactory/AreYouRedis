import streamlit as st
import asyncio
import calendar
import datetime
import pandas as pd
import plotly.express as px

from utils.widgets import update_session_state_var
from utils.graph import (
    get_graph_data,
    get_arc_graph
)
from src.redis_db import execute_user_query
from config_files import config


def get_user_search_query():
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
            min_value=2000,
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
            options=['Machine learning'],
            default=st.session_state.categories,
            key='categories_multiselect',
            on_change=update_session_state_var,
            kwargs={
                'session_state_var_name': 'categories',
                'widget_key': 'categories_multiselect'
            }
        )


@st.experimental_memo
def get_search_query_results(user_search_query, k_similar, year_min, year_max, categories):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return execute_user_query(
        user_text=user_search_query,
        k=k_similar,
        year_min=year_min,
        year_max=year_max,
        categories=[config.arxiv_categories_mapping[category] + "*" for category in categories]
    )


@st.experimental_memo
def display_topic_trend(query_results):
    # dates = [datetime.datetime(int(el['year']), int(el['month']), 1) for el in query_results]
    dates = [int(el['year']) for el in query_results]
    weights = [1 for _ in query_results]
    time_series_df = pd.DataFrame(
        {
            'date': dates,
            'count_papers': weights
        }
    )
    time_series_df = time_series_df.groupby('date').sum().reset_index()
    fig = px.line(time_series_df, x='date', y='count_papers')
    st.plotly_chart(
        fig,
        use_container_width=True
    )


def display_arc_graph(query_results):
    graph_fig = get_arc_graph(get_graph_data(query_results))
    st.plotly_chart(
        figure_or_data=graph_fig,
        use_container_width=True
    )


def display_search_query_results(user_search_query_results):
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
    user_search_query_results_sorted = sorted(user_search_query_results, key=lambda d: d['year'] + '-' + d['month'])
    papers_ids_sorted_by_date = [paper['paper_id'] for paper in user_search_query_results_sorted]
    for i in range(len(user_search_query_results)):
        res = user_search_query_results[i]
        st.markdown(
            f"""
            <a id="section-{papers_ids_sorted_by_date.index(res['paper_id'])}">\n</a>
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
                    f"**Abstract:** {res['abstract']}  \n"
                    f"[Go to paper](https://arxiv.org/abs/{res['paper_id']})"
                )
            )
