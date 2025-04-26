import streamlit as st
from Utils import user, utils  # Import user.py from the Utils folder
from anthropic_menu import recommend_food

# Set page config
st.set_page_config(page_title="Restaurant Menus", layout="centered")

# Add custom CSS to set background color for the container

if "restaurants" not in st.session_state:
    st.session_state.restaurants = []

    # Initialize session state if it doesn't exist
if "restrictions_to_add" not in st.session_state:
    st.session_state.restrictions_to_add = []

if "user" not in st.session_state:
    st.session_state.user = user.User("Test User", {})  # <-- Now creating User object

if "active_restaurant" not in st.session_state:
    st.session_state.active_restaurant = None

if "cached_restaurant_recs" not in st.session_state:
    st.session_state.cached_restaurant_recs = {}

st.title("Restaurant Menus" if st.session_state.active_restaurant == None else st.session_state.restaurants[st.session_state.active_restaurant].get_restaurant() + " Menu")

def update_active_restaurant(index):
    st.session_state.active_restaurant = index

def make_active_restaurant_setter(index):
    return lambda: update_active_restaurant(index)

def score_to_opinion(value):
    if value == 1.0:
        return ("Perfect", 'blue')
    elif value >= 0.8:
        return ("Okay", 'green')
    else:
        return ("Avoid", 'red')

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
            c.button("Menu", key=restaurant.get_restaurant() + "_menubutton", type="primary", use_container_width=True, on_click=make_active_restaurant_setter(i))

            col_write = (col_write + 1) % 3
else:
    # Get the recommendations for this user at this restaurant.
    recommendations = "Unchosen"
    if st.session_state.restaurants[st.session_state.active_restaurant].get_restaurant() not in st.session_state.cached_restaurant_recs:
        recommendations = recommend_food(st.session_state.restaurants[st.session_state.active_restaurant], st.session_state.user)
        st.session_state.cached_restaurant_recs[st.session_state.restaurants[st.session_state.active_restaurant].get_restaurant()] = recommendations    
    else:
        recommendations = st.session_state.cached_restaurant_recs[st.session_state.restaurants[st.session_state.active_restaurant].get_restaurant()]

    for dish, (score, reason) in recommendations.items():
        c = st.container(border = True)
        with c:
            c1, c2, c3 = st.columns(3)
            opinion = score_to_opinion(score)

            c1.badge(f"{dish}", color=opinion[1])
            c2.markdown(f'<p style="color: {opinion[1]};">{opinion[0]}</p>', unsafe_allow_html=True, help=reason)

            price = -1
            for test_dish in st.session_state.restaurants[st.session_state.active_restaurant].get_menu():
                if test_dish.get_dish() == dish:
                    price = test_dish.get_price()

            c3.text(f"${'{0:.2f}'.format(price)}")
    
    st.button("Back to List", update_active_restaurant(None))