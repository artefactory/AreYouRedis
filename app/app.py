import streamlit as st

from utils.display import (
    display_logo,
    display_main_title,
    display_section_title
)
from config_files import (
    config
)
import page_example
import paper_search
from utils.widgets import update_session_state_var


def main():
    """
    App entry point.
    """

    config.setup()

    # --- Sidebar containers --- #
    logo_container = st.sidebar.container()
    page_choice_section_title_container = st.sidebar.container()
    pages_choice_container = st.sidebar.container()

    # --- Page containers --- #
    page_title_container = st.container()
    page_content_container = st.container()

    # --- Variables --- #
    PAGES = {
        "Page example": page_example,
        "Paper search": paper_search
    }

    # --- Sidebar --- #
    with logo_container:
        display_logo()

    with page_choice_section_title_container:
        display_section_title("PAGE SELECTION", 'small')

    with pages_choice_container:
        st.radio(
            label="Go to",
            options=list(PAGES.keys()),
            index=list(PAGES.keys()).index(st.session_state.selected_page),
            key='selected_page_radio',
            on_change=update_session_state_var,
            kwargs={
                'session_state_var_name': 'selected_page',
                'widget_key': 'selected_page_radio'
            }
        )

    # --- Page --- #
    with page_title_container:
        display_main_title()

    with page_content_container:
        PAGES[st.session_state.selected_page].main()


if __name__ == "__main__":
    main()
