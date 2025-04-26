import streamlit as st
from streamlit_tags import st_tags
from Utils import user  # Import user.py from the Utils folder

# Set page config
st.set_page_config(page_title="Ingredient Restrictions", layout="centered")

if "restaurants" not in st.session_state:
    st.session_state.restaurants = []

    # Initialize session state if it doesn't exist
if "restrictions_to_add" not in st.session_state:
    st.session_state.restrictions_to_add = []

if "user" not in st.session_state:
    st.session_state.user = user.User("Test User", {})  # <-- Now creating User object

if "cached_restaurant_recs" not in st.session_state:
    st.session_state.cached_restaurant_recs = {}

st.title("Add Ingredient Restrictions")

def edit_ing(ingredient_name, value):
    st.session_state.cached_restaurant_recs = {}
    st.session_state.user.change_restriction(ingredient_name, value)

def edit_ing_maker(ingredient_name, value):
    return lambda: edit_ing(ingredient_name, value)

def delete_ing(ingredient_name):
    st.session_state.cached_restaurant_recs = {}
    st.session_state.user.remove_restriction(ingredient_name)

def delete_ing_maker(ingredient_name):
    return lambda: delete_ing(ingredient_name)

# Function to show the ingredient in a container with a border and two columns
def show_ingredient(ingredient_name, severity):
    with st.container(border=True):
        # Create two main columns inside the container
        col1, col2, col3 = st.columns([1, 3, 1])

        # First column: display the ingredient name
        with col1:
            st.badge(ingredient_name.capitalize(), color="grey")

        # Second column: add three buttons horizontally across the column
        with col2:
            subcol1, subcol2, subcol3 = st.columns(3)
            with subcol1:
                st.button("Dislike", key=f"{ingredient_name}_btn_1", use_container_width=True, type="primary" if severity == 1 else "secondary",
                          on_click=edit_ing_maker(ingredient_name, 1))
            with subcol2:
                st.button("Unsafe", key=f"{ingredient_name}_btn_2", use_container_width=True, type="primary" if severity == 2 else "secondary",
                          on_click=edit_ing_maker(ingredient_name, 2))
            with subcol3:
                st.button("Severe", key=f"{ingredient_name}_btn_3", use_container_width=True, type="primary" if severity == 3 else "secondary",
                          on_click=edit_ing_maker(ingredient_name, 3))
        
        with col3:
            _, _, c3 = st.columns([1, 1, 2])
            with c3:
                st.button("🗑️", key=f"{ingredient_name}_trash", on_click=delete_ing_maker(ingredient_name))

# Tags input with updated label and suggestions
tags = st_tags(
    label="Enter ingredients to avoid:",
    value=st.session_state.restrictions_to_add, 
    suggestions=[
        "Peanuts", "Tree nuts", "Dairy", "Eggs", "Gluten", "Soy", "Wheat", 
        "Fish", "Shellfish", "Sesame seeds", "Pork", "Beef", "Chicken", 
        "Alcohol", "Sugar", "Caffeine", "Fruits", "Plums"
    ],
    key="ingredient_tags"
)

# Button to add restrictions
if st.button("Add Restrictions"):
    # Add tags from restrictions_to_add to restrictions with duplicate protection
    for tag in st.session_state.restrictions_to_add:
        st.session_state.user.add_restriction(tag, 3)
    
    # Clear the tags input by resetting restrictions_to_add
    st.session_state.restrictions_to_add = []

    st.session_state.cached_restaurant_recs = {}

# Save tags to session state
st.session_state.restrictions_to_add = tags

# Display current restrictions using the show_ingredient function
st.subheader("Your Restrictions:")
if st.session_state.user.get_dietary_restrictions():
    for ing_name, severity in st.session_state.user.get_dietary_restrictions().items():
        show_ingredient(ing_name, severity)
else:
    st.write("No restrictions added yet.")
