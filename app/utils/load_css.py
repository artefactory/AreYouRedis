import streamlit as st


def local_css(filepath):
    """
    Import css style file in the current html page.

    Parameters
    ----------
    filepath : str
        Path of the css style file.
    """
    with open(filepath) as f:
        st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)


def color_markdown(markdown, style_class='atf-red'):
    """
    Format a markdown with specified style_class.

    Parameters
    ----------
    markdown : str
        Text content.
    style_class  : str
        Style class. Must be in ['atf-blue', 'atf-red', 'atf-turquoise']
    """
    markdown = f"<div><span class={style_class}>{markdown}</span></div>"
    return markdown
