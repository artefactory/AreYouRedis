import streamlit as st
import asyncio
import calendar

from utils.widgets import update_session_state_var
from src.redis_db import execute_user_query


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


@st.experimental_memo
def get_search_query_results(user_search_query):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return execute_user_query(st.session_state.user_search_query)


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
    for i in range(len(user_search_query_results)):
        res = user_search_query_results[i]
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
                    f"**Abstract:** {res['abstract']}  \n"
                    f"[Go to paper](https://arxiv.org/abs/{res['paper_id']})"         
                )
            )
