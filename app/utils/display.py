import streamlit as st

from config_files import (
    config
)
from utils.load_css import (
    color_markdown
)


def display_logo():
    """
    Display logo.
    """
    st.image(
        image=config.LOGO_PATH
    )


def display_main_title():
    """
    Display main title.
    """
    st.markdown(
        "<h2 style='text-align: center; color: #ff0066; '>Redis Search</h2>",
        unsafe_allow_html=True
    )


def display_section_title(title, type):
    """
    Display section title.

    Parameters
    ----------
    title : str
        Title content.
    type : str
        Title type. Can be either 'small' or 'large'.
    """
    if type == "small":
        st.markdown(color_markdown(title), unsafe_allow_html=True)

    elif type == "large":
        st.markdown(color_markdown(
            "<div class='atf-red'>" + title + "</div>",
            style_class='atf-red-header'
        ), unsafe_allow_html=True)
