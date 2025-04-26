import streamlit as st
from Utils import user, utils  # Import user.py from the Utils folder

# Set page config
st.set_page_config(page_title="Restaurant Menus", layout="centered")

if "restaurants" not in st.session_state:
    st.session_state.restaurants = []

    # Initialize session state if it doesn't exist
if "restrictions_to_add" not in st.session_state:
    st.session_state.restrictions_to_add = []

if "user" not in st.session_state:
    st.session_state.user = user.User("Test User", {})  # <-- Now creating User object

if "active_restaurant" not in st.session_state:
    st.session_state.active_restaurant = None

st.title("Restaurant Menus")

def update_active_restaurant(index):
    st.session_state.active_restaurant = index

def make_active_restaurant_setter(index):
    return lambda: update_active_restaurant(index)

if st.session_state.active_restaurant is None:
    if len(st.session_state.restaurants) == 0:
        st.warning("No restaurants set up yet. Head over to Add Restaurant and add some!")
    else:
        col0, col1, col2 = st.columns(3)
        col_write = 0
        for i in range(len(st.session_state.restaurants)):
            restaurant = st.session_state.restaurants[i]
            c = ([col0, col1, col2])[col_write].container(border = True)
            c.write(restaurant.get_restaurant())
            c.button("Menu", key=restaurant.get_restaurant() + "_menubutton", type="primary", on_click=make_active_restaurant_setter(i))

            col_write = (col_write + 1) % 3
else:
    pass