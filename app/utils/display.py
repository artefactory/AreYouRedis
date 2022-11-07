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
    _, redis_logo_col, _, artefact_logo_col, _, saturn_logo_col, _ = st.columns(7)
    artefact_logo_col.image(
        image=config.ARTEFACT_LOGO_PATH
    )
    redis_logo_col.image(
        image=config.REDIS_LOGO_PATH
    )
    saturn_logo_col.image(
        image=config.SATURN_LOGO_PATH
    )


def display_main_title():
    """
    Display main title.
    """
    st.markdown(
        "<h1 style='text-align: center; color: #49b6c2; '>Darwinian Paper Explorer</h1>",
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

    if type == "tab_header":
        st.markdown(
            f"<h5 style='text-align: center; color: #49b6c2; '>{title}</h5>",
            unsafe_allow_html=True
        )

    elif type == "large":
        st.markdown(color_markdown(
            "<div class='atf-red'>" + title + "</div>",
            style_class='atf-red-header'
        ), unsafe_allow_html=True)


def remove_paddings_top():
    """
    Remove padding at the top of the page (sidebar and page).
    """
    st.write('<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)
    st.write('<style>div.block-container{padding-bottom:2rem;}</style>', unsafe_allow_html=True)
    st.write('<style>.css-hxt7ib{padding-top:2rem;}</style>', unsafe_allow_html=True)
