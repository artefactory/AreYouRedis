import streamlit as st


def update_session_state_var(session_state_var_name, widget_key):
    """
    Update session state variable.

    Parameters
    ----------
    session_state_var_name : str
        Name of the session state variable.
    widget_key : str
        Key of the widget from which the new value is to be retrieved.
    """
    if widget_key in st.session_state:
        st.session_state[session_state_var_name] = st.session_state[widget_key]
