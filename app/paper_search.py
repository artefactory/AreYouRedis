import streamlit as st

from utils.display import (
    display_section_title
)
from features.basic_search import (
    get_user_search_query,
    get_search_query_results,
    display_search_query_results
)


def main():
    """
    Home page main function.
    """
    # --- Page containers --- #
    search_section_title_container = st.container()
    search_query_input_container = st.container()
    execute_seach_query_container = st.container()
    search_papers_display_container = st.container()

    # --- Page --- #
    with search_section_title_container:
        display_section_title("Basic search", "large")

    with search_query_input_container:
        get_user_search_query()

    with execute_seach_query_container:
        if len(st.session_state.user_search_query) > 0:
            st.session_state.user_search_query_results = get_search_query_results(st.session_state.user_search_query)
        else:
            st.session_state.user_search_query_results = []

    with search_papers_display_container:
        if st.session_state.user_search_query_results is not None and len(st.session_state.user_search_query_results) > 0:
            display_search_query_results(st.session_state.user_search_query_results)
