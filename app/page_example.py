import streamlit as st

from utils.display import (
    display_section_title
)


def main():
    """
    Home page main function.
    """
    # --- Page containers --- #
    load_section_title_container = st.container()
    query_input_container = st.container()

    # --- Page --- #
    with load_section_title_container:
        display_section_title("Enter your query", "large")

    with query_input_container:
        st.text_input(label="Enter query")
