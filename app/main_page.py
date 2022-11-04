import streamlit as st

from utils.display import (
    display_section_title
)
from features.topic_evolution import (
    get_user_search_query,
    get_search_filters,
    get_search_query_results,
    display_search_query_results,
    display_topic_trend,
    display_arc_graph
)


def main():
    """
    Home page main function.
    """
    # --- Page containers --- #
    search_section_title_container = st.container()
    search_query_input_container = st.container()
    search_filters_container = st.container()
    execute_seach_query_container = st.container()
    topic_trend_container = st.container()
    topic_arc_graph_container = st.container()
    search_papers_display_container = st.container()

    # --- Page --- #
    with search_section_title_container:
        display_section_title("Search parameters", "large")

    with search_query_input_container:
        get_user_search_query()

    with search_filters_container:
        get_search_filters()

    with execute_seach_query_container:
        if len(st.session_state.user_search_query) > 0:
            st.session_state.user_search_query_results = get_search_query_results(
                user_search_query=st.session_state.user_search_query,
                k_similar=st.session_state.k_similar,
                year_min=st.session_state.year_min,
                year_max=st.session_state.year_max,
                categories=st.session_state.categories
            )
        else:
            st.session_state.user_search_query_results = []

    with topic_trend_container:
        if len(st.session_state.user_search_query_results) > 1 and len(st.session_state.user_search_query) > 0:
            display_section_title("Topic trend and future projection", "large")
            display_topic_trend(
                query_results=st.session_state.user_search_query_results
            )
        elif len(st.session_state.user_search_query) == 0:
            pass
        else:
            st.warning('Your query has one or less related papers. Please use less restrictive filter or change your query.')

    with topic_arc_graph_container:
        if len(st.session_state.user_search_query_results) > 1 and len(st.session_state.user_search_query) > 0:
            display_section_title("Topic evolution", "large")
            display_arc_graph(
                query_results=st.session_state.user_search_query_results
            )
        else:
            pass

    with search_papers_display_container:
        if st.session_state.user_search_query_results is not None and len(st.session_state.user_search_query_results) > 0:
            display_section_title("Papers overview (ordered by similarity)", "large")
            display_search_query_results(st.session_state.user_search_query_results)
