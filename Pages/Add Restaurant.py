import streamlit as st
from Utils import user, utils  # Import user.py from the Utils folder

# Set page config
st.set_page_config(page_title="Menu Upload", layout="centered")

if "restaurants" not in st.session_state:
    st.session_state.restaurants = []

    # Initialize session state if it doesn't exist
if "restrictions_to_add" not in st.session_state:
    st.session_state.restrictions_to_add = []

if "user" not in st.session_state:
    st.session_state.user = user.User("Test User", {})  # <-- Now creating User object


st.title("Upload New Menu")

# Set restaurant's name
active_restaurant_name = st.text_input("Restaurant Name")

# Upload restaurant's menu
menu_pdf = st.file_uploader("Upload Menu PDF", type="pdf")

# Confirm button
ready = active_restaurant_name != "" and menu_pdf is not None
if st.button("Add Restaurant", disabled = not ready) and active_restaurant_name is not None and menu_pdf is not None:
    restaurant_object = utils.from_pdf_to_restaurant(menu_pdf, active_restaurant_name)
    st.write(restaurant_object.get_restaurant())
    _ = [st.write(item.list_information()) for item in restaurant_object.get_menu()]

    st.session_state.restaurants.append(restaurant_object)