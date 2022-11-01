import streamlit as st
import os

from utils.load_css import (
    local_css
)


BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOGO_PATH = os.path.join(BASE_PATH, "style", "Artefact_logo.png")
SMALL_LOGO_PATH = os.path.join(BASE_PATH, "style", "Artefact_small_logo.jpeg")
STYLE_FILE_PATH = os.path.join(BASE_PATH, "style", "style.css")


# Session state variables dict with default values
default_val_session_state_vars_dict = {
    # --- Widgets' variables to be persisted --- #
    'selected_page': 'Page example',
    'user_search_query': '',
    'user_search_query_results': []
}


def setup():
    """
    Set up streamlit application
    """
    st.set_page_config(
        page_title="Paper trends",
        page_icon=SMALL_LOGO_PATH,
        layout="wide"
    )

    local_css(STYLE_FILE_PATH)

    for var_name, default_value in default_val_session_state_vars_dict.items():
        if var_name not in st.session_state:
            st.session_state[var_name] = default_value
