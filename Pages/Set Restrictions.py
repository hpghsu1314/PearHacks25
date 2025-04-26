import streamlit as st
from streamlit_tags import st_tags
from Utils import user  # Import user.py from the Utils folder

# Set page config
st.set_page_config(page_title="Ingredient Restrictions", layout="centered")

# Initialize session state if it doesn't exist
if "restrictions" not in st.session_state:
    st.session_state.restrictions = []

if "restrictions_to_add" not in st.session_state:
    st.session_state.restrictions_to_add = []

if "active_user" not in st.session_state:
    st.session_state.active_user = user.User("Test User", {})  # <-- Now creating User object

st.title("Add Ingredient Restrictions")

# Function to show the ingredient in a container with a border and two columns
def show_ingredient(ingredient_name):
    with st.container(border=True):
        # Create two main columns inside the container
        col1, col2 = st.columns(2)

        # First column: display the ingredient name
        with col1:
            st.write(ingredient_name)

        # Second column: add three buttons horizontally across the column
        with col2:
            subcol1, subcol2, subcol3 = st.columns(3)
            with subcol1:
                st.button("1", key=f"{ingredient_name}_btn_1", use_container_width=True)
            with subcol2:
                st.button("2", key=f"{ingredient_name}_btn_2", use_container_width=True)
            with subcol3:
                st.button("3", key=f"{ingredient_name}_btn_3", use_container_width=True)

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
        if tag not in st.session_state.restrictions:
            st.session_state.restrictions.append(tag)
    
    # Clear the tags input by resetting restrictions_to_add
    st.session_state.restrictions_to_add = []

# Save tags to session state
st.session_state.restrictions_to_add = tags

# Display current restrictions using the show_ingredient function
st.subheader("Your Restrictions:")
if st.session_state.restrictions:
    for item in st.session_state.restrictions:
        show_ingredient(item)
else:
    st.write("No restrictions added yet.")
