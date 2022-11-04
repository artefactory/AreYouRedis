import streamlit as st
import main_page

from utils.display import (
    display_logo,
    display_main_title,
    remove_paddings_top
)
from config_files import (
    config
)


def main():
    """
    App entry point.
    """

    config.setup()

    # --- Page containers --- #
    logo_container = st.container()
    page_title_container = st.container()
    page_content_container = st.container()

    # --- Sidebar --- #
    with logo_container:
        remove_paddings_top()
        display_logo()

    # --- Page --- #
    with page_title_container:
        display_main_title()

    with page_content_container:
        main_page.main()


if __name__ == "__main__":
    main()
