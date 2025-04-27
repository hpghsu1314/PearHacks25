# Home page. Explains what the app does, slick logo, where to go, etc.

import streamlit as st
from Utils import user  # Import user.py from the Utils folder

# Set page configuration
st.set_page_config(page_title="Awning", page_icon=":sparkles:")

if "restaurants" not in st.session_state:
    st.session_state.restaurants = []

    # Initialize session state if it doesn't exist
if "restrictions_to_add" not in st.session_state:
    st.session_state.restrictions_to_add = []

if "user" not in st.session_state:
    st.session_state.user = user.User("Test User", {})  # <-- Now creating User object


# Display logo and app name
# Open center-align div

# Create three columns
_, col2, _ = st.columns([1, 2, 1])  # Center column is a bit wider

# Place the image in the center column
with col2:
    st.image("awning-logo.png", use_container_width=True)


# Optional: Some welcome text
st.subheader("Got allergies? Never ask for an ingredients list again.")
st.write("Welcome to Awning, your solution to managing dietary restrictions.")
st.write("With Awning, you can set your restrictions any any ingredient. Then, enjoy LLM-powered recommendations for dishes at your favorite restaurants.")
""

st.subheader("Features")
"""
⏩ Add and manage your dietary restrictions.  
⏩ Extract dishes from a a picture or PDF of any menu.  
⏩ Use the power of AI to see potential allergens.  
⏩ Get personally-tailored LLM recommendations for safe dishes at all your favorite restaurants.
"""
