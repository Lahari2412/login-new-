
import streamlit as st
import requests
import json
from pathlib import Path
from streamlit_extras.switch_page_button import switch_page
from streamlit.source_util import _on_pages_changed, get_pages

st.set_page_config(layout="wide")

# Initialize session state for login status
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Load all pages
def get_all_pages():
    default_pages = get_pages("login.py")
    pages_path = Path("pages.json")
    if pages_path.exists():
        saved_default_pages = json.loads(pages_path.read_text())
    else:
        saved_default_pages = default_pages.copy()
        pages_path.write_text(json.dumps(default_pages, indent=4))
    return saved_default_pages

# Clear all pages but not the login page
def clear_all_but_default_page():
    current_pages = get_pages("login.py")
    if len(current_pages.keys()) == 1:
        return
    get_all_pages()
    key, val = list(current_pages.items())[0]
    current_pages.clear()
    current_pages[key] = val
    _on_pages_changed.send()

# Show all pages
def show_all_pages():
    current_pages = get_pages("login.py")
    saved_pages = get_all_pages()
    for key in saved_pages:
        if key not in current_pages:
            current_pages[key] = saved_pages[key]
    _on_pages_changed.send()

# Hide specific page
def hide_page(name: str):
    current_pages = get_pages("login.py")
    for key, val in current_pages.items():
        if val["page_name"] == name:
            del current_pages[key]
            _on_pages_changed.send()
            break

# Clear all but the login page on start
clear_all_but_default_page()


# Login function
def login(email, password):
    url = "http://localhost:8083/api/v1/login/"
    payload = {"email": email, "password": password}
    response = requests.post(url, json=payload)
    return response

# Streamlit login page
st.title("Login")

email = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    response = login(email, password)
    if response.status_code == 200:
        st.success("Login successful")
        st.session_state.logged_in = True
        # Show all pages after successful login
        show_all_pages()
        # Redirect to home page
        switch_page("home")
    elif response.status_code == 401:
        st.error("Invalid username or password. Please try again.")
    elif response.status_code == 404:
        st.error("User not found. Please sign up.")
        # Redirect to sign up page
        switch_page("signup")
    else:
        st.error("Login failed. Please check your credentials or try again later.")

# Link to sign up page
if st.button("Sign Up"):
    show_all_pages()
    switch_page("signup")
