# Home page. Explains what the app does, slick logo, where to go, etc.

import streamlit as st

# Set page configuration
st.set_page_config(page_title="Allergy App", page_icon=":sparkles:")


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