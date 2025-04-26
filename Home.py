# Home page. Explains what the app does, slick logo, where to go, etc.

import streamlit as st
from Utils import user  # Import user.py from the Utils folder

# Set page configuration
st.set_page_config(page_title="Allergy App", page_icon=":sparkles:")

if "restaurants" not in st.session_state:
    st.session_state.restaurants = []

    # Initialize session state if it doesn't exist
if "restrictions_to_add" not in st.session_state:
    st.session_state.restrictions_to_add = []

if "user" not in st.session_state:
    st.session_state.user = user.User("Test User", {})  # <-- Now creating User object


# Display logo and app name

# Placeholder for the logo
st.image("https://via.placeholder.com/80", width=80)  # You can replace this URL with your actual logo

st.markdown(
"<h1 style='text-align: center;'>Allergy App</h1>",
    unsafe_allow_html=True
)

# Divider
st.markdown("---")

# Optional: Some welcome text
st.write("Welcome to the Untitled app! 🚀")